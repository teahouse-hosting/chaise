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
async def basic_session(basic_pool):
    return await basic_pool.session()


@pytest.fixture
async def basic_database(basic_session, generate_dbname):
    dbname = generate_dbname()
    db = await basic_session.create_db(dbname)
    yield db
    await basic_session.delete_db(dbname)
