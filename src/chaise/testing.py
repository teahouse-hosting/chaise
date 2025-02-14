"""
Provides utilities for testing
"""

import contextlib
import functools
from pathlib import Path
import socket
import sys
import typing

import anyio
import docker
import docker.utils
import httpx


class ContextNotExistError(ValueError):
    """
    The given context does not exist
    """


def _docker_3190_workaround():
    """
    Work around for https://github.com/docker/docker-py/issues/3190
    """
    if docker.utils.config.find_config_file() is None:
        # TODO: Prefer .config_path_from_environment() over .home_dir()
        config_path = (
            Path(docker.utils.config.home_dir())
            / docker.utils.config.DOCKER_CONFIG_FILENAME
        )

        if config_path.parent.exists():
            # If .docker doesn't exist, it doesn't contain contexts
            config_path.touch()


@functools.cache
def _get_docker_client(use: str | None = None) -> docker.DockerClient:
    """
    Get a docker client for the given docker context.

    Unlike docker.from_env(), this considers the user's configured context.
    """
    _docker_3190_workaround()

    context = docker.ContextAPI.get_context(use)
    if context is None:
        raise ContextNotExistError(f"Docker context {use!r} not found")
    return docker.DockerClient(
        base_url=context.endpoints["docker"]["Host"], tls=context.TLSConfig
    )


# https://stackoverflow.com/a/45690594
def _find_free_port():
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@contextlib.contextmanager
def spawn_docker_couchdb() -> typing.Iterator[str]:
    """
    Creates a tempory CouchDB instance using docker, and automatically cleans it up.

    Returns the URL by which it's accessible.
    """
    client = _get_docker_client()

    couch_container = client.containers.run(
        detach=True,
        image="ghcr.io/teahouse-hosting/quick-and-dirty-couch:latest",
        auto_remove=True,
        environment={
            "COUCHDB_USER": "admin",
            "COUCHDB_PASSWORD": "admin",
        },
        ports={"5984/tcp": None},
    )
    # TODO: Stream container stdout

    couch_container.reload()

    # Dig out the connected port
    port_config = couch_container.attrs["NetworkSettings"]["Ports"]["5984/tcp"][0]
    couch_ip = port_config["HostIp"]
    if couch_ip == "0.0.0.0":
        couch_ip = "127.0.0.1"
    elif couch_ip == "::":
        couch_ip = "::1"
    couch_port = port_config["HostPort"]

    try:
        yield f"http://admin:admin@{couch_ip}:{couch_port}/"
    finally:
        couch_container.stop()


async def wait_for_readiness(couch_url: str, *, timeout: float = 60) -> None:
    """
    Waits for a CouchDB instance to actually initialize and be ready to accept
    requests.

    Raises TimeoutError on failure.
    """
    timeout_increment = 0.1
    url = httpx.URL(couch_url).join("_up")
    client = httpx.AsyncClient()
    for _ in range(int(timeout / timeout_increment)):
        try:
            resp = await client.get(url)
        except httpx.RequestError:
            await anyio.sleep(timeout_increment)
        else:
            if resp.is_success:
                return
            else:
                await anyio.sleep(timeout_increment)
    else:
        raise TimeoutError(f"Timeout waiting for CouchDB to initialize ({couch_url})")


async def _call_cli(couch_url, *argv):
    oldargv = sys.argv
    try:
        sys.argv = ["chaise", "--verbose", "--server", couch_url, *argv]
        import chaise.cli

        await chaise.cli.main()
    finally:
        sys.argv = oldargv


@contextlib.asynccontextmanager
async def run_cli_apply(couch_url: str, dbs_module: str):
    """
    Runs the apply CLI command, and then cleans up databases afterwards.
    """
    await _call_cli(couch_url, "apply", dbs_module)
    yield
    # TODO: Look up what databases were actually defined
    from chaise.cli.client import ConstantPool

    session = await ConstantPool(couch_url).session()
    dbs = {db async for db in session.iter_dbs() if not db.startswith("_")}
    for db in dbs:
        await session.delete_db(db)
