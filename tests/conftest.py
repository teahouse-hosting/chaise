import os
import random
import subprocess

import anyio
import httpx
import pytest


@pytest.fixture(scope="session")
def _couch_url():
    """
    Makes sure there's a CouchDB instance running and available
    """
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
                "5984:5984",
                "ghcr.io/teahouse-hosting/quick-and-dirty-couch:latest",
            ],
        )
        yield "http://admin:admin@127.0.0.1:5984/"
        proc.terminate()


@pytest.fixture(scope="module")  # Would be session, but anyio_backend is module
async def couch_url(_couch_url):
    url = httpx.URL(_couch_url).join("_up")
    client = httpx.AsyncClient()
    while True:
        try:
            resp = await client.get(url)
        except httpx.RequestError:
            await anyio.sleep(0.1)
        else:
            if resp.is_success:
                return _couch_url
            else:
                await anyio.sleep(0.1)


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
