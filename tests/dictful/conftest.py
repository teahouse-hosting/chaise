import pytest

import chaise.dictful


class ConstantPool(chaise.dictful.BasicPool):
    def __init__(self, url: str):
        self.url = url
        super().__init__()

    async def iter_servers(self):
        yield self.url


@pytest.fixture
def basic_pool(couch_url):
    return ConstantPool(couch_url)


@pytest.fixture
async def basic_database(basic_pool, generate_dbname):
    session = await basic_pool.session()
    # Not actually secret, just the simplest way to generate a name
    dbname = generate_dbname()
    # TODO: Use native session methods, when they're written
    await session._request("PUT", dbname)
    yield dbname
    await session._request("DELETE", dbname)
