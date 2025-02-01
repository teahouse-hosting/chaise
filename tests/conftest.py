import os
import random
import sys

import pytest


@pytest.fixture(scope="module")  # This is so cli gets its own
def _couch_url():
    """
    Makes sure there's a CouchDB instance running and available
    """
    from chaise.testing import spawn_docker_couchdb

    if url := os.environ.get("COUCHDB_URL", None):
        # One was handed to us by the environment. Just use that.
        print("env")
        yield url
    else:
        print("docker")
        with spawn_docker_couchdb() as url:
            yield url


@pytest.fixture(scope="module")  # Would be session, but anyio_backend is module
async def couch_url(_couch_url):
    from chaise.testing import wait_for_readiness

    print(_couch_url)
    await wait_for_readiness(_couch_url)
    return _couch_url


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
