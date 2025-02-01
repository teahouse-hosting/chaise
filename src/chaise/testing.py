"""
Provides utilities for testing
"""

import contextlib
import functools
from pathlib import Path
import socket
import subprocess
import sys
import typing

import anyio
import docker
import docker.errors
import docker.models.images
import docker.types
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

    BUG: Instead of finding a free port, this always uses port 5984. See
    https://github.com/teahouse-hosting/quick-and-dirty-couch/issues/1
    """
    port = _find_free_port()
    # FIXME: We can't set the couch port quickly from outside
    port = 5984

    # Spawn a container
    proc = subprocess.Popen(
        [
            "docker",
            "run",
            "--rm",
            "-e",
            "COUCHDB_USER=admin",
            "-e",
            "COUCHDB_PASSWORD=admin",
            "-p",
            f"{port}:{port}",
            "ghcr.io/teahouse-hosting/quick-and-dirty-couch:latest",
        ],
        stdin=subprocess.DEVNULL,
        stdout=sys.stderr,
        stderr=sys.stderr,
    )
    try:
        yield f"http://admin:admin@127.0.0.1:{port}/"
    finally:
        proc.terminate()
        proc.wait()


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
