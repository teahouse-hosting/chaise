import types

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


class DictRegistry(chaise.dictful.DictRegistry):
    pass


class DictSession(chaise.CouchSession):
    loader = DictRegistry


class DictPool(chaise.SessionPool):
    session_class = DictSession

    def __init__(self, url: str):
        self.url = url
        super().__init__()

    async def iter_servers(self):
        yield self.url


@pytest.fixture(scope="session")
def dict_models():
    @DictRegistry.document("Foo1")
    class AncientFoo(chaise.dictful.Document):
        # spam is uppercase
        pass

    @DictRegistry.document("Foo2")
    class OldFoo(chaise.dictful.Document):
        # spam is lowercase
        pass

    @DictRegistry.migration(AncientFoo, OldFoo)
    def foo1_migration(old):
        return OldFoo(bar=old["bar"].lower())

    @DictRegistry.document("Foo3")
    class Foo(chaise.dictful.Document):
        # spam is titlecase
        pass

    @DictRegistry.migration(OldFoo, Foo)
    def foo2_migration(old):
        return Foo(bar=old["bar"].title())

    @DictRegistry.document("Counter")
    class Counter(chaise.dictful.Document):
        pass

    return types.SimpleNamespace(
        Foo=Foo,
        AncientFoo=AncientFoo,
        OldFoo=OldFoo,
        Counter=Counter,
    )


@pytest.fixture
def dict_pool(couch_url):
    return DictPool(couch_url)


@pytest.fixture
async def dict_session(dict_pool):
    return await dict_pool.session()


@pytest.fixture
async def dict_database(dict_session, generate_dbname):
    dbname = generate_dbname()
    db = await dict_session.create_db(dbname)
    yield db
    await dict_session.delete_db(dbname)
