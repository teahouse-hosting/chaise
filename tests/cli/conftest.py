import pytest

import chaise.dictful
import chaise.cli.client


@pytest.fixture
def cli_pool(couch_url):
    return chaise.cli.client.ConstantPool(couch_url)


@pytest.fixture
async def cli_session(cli_pool):
    return await cli_pool.session()
