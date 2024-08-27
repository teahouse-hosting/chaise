import os
import random
import subprocess
import sys

from contextlib import closing
import socket

import anyio
import httpx
import pytest


# https://stackoverflow.com/a/45690594
def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@pytest.fixture(scope="module")  # This is so cli gets its own
def _couch_url():
    """
    Makes sure there's a CouchDB instance running and available
    """
    port = find_free_port()
    # FIXME: We can't set the couch port quickly from outside
    port = 5984
    if url := os.environ.get("COUCHDB_URL", None):
        # One was handed to us by the environment. Just use that.
        yield url
    else:
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
        )
        yield f"http://admin:admin@127.0.0.1:{port}/"
        proc.terminate()
        proc.wait()


@pytest.fixture(scope="module")  # Would be session, but anyio_backend is module
async def couch_url(_couch_url):
    url = httpx.URL(_couch_url).join("_up")
    client = httpx.AsyncClient()
    for _ in range(50):
        try:
            resp = await client.get(url)
        except httpx.RequestError:
            await anyio.sleep(0.1)
        else:
            if resp.is_success:
                return _couch_url
            else:
                await anyio.sleep(0.1)
    else:
        raise TimeoutError(f"Timeout waiting for CouchDB to initialize ({_couch_url})")


@pytest.fixture(scope="session")
def generate_dbname():
    def generate_dbname():
        return "".join(
            [
                random.choice("abcdefghijklmnopqrstuvqxyz"),
                *random.choices("abcdefghijklmnopqrstuvqxyz0123456789", k=5),
            ]
        )

    return generate_dbname


@pytest.fixture
async def cli(couch_url):
    async def call(*argv):
        oldargv = sys.argv
        try:
            sys.argv = ["chaise", "--verbose", "--server", couch_url, *argv]
            import chaise.cli

            await chaise.cli.main()
        finally:
            sys.argv = oldargv

    return call
