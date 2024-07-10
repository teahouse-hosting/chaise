import attrs
import pytest
import types

import chaise
import chaise.attrs


class AttrsRegistry(chaise.attrs.AttrsRegistry):
    pass


class AttrsSession(chaise.CouchSession):
    loader = AttrsRegistry


class AttrsPool(chaise.SessionPool):
    session_class = AttrsSession

    def __init__(self, url: str):
        self.url = url
        super().__init__()

    async def iter_servers(self):
        yield self.url


@pytest.fixture(scope="session")
def attrs_models():
    @AttrsRegistry.document("Foo1")
    @attrs.define
    class AncientFoo(chaise.dictful.Document):
        # spam is uppercase
        pass

    @AttrsRegistry.document("Foo2")
    @attrs.define
    class OldFoo(chaise.dictful.Document):
        # spam is lowercase
        pass

    @AttrsRegistry.migration(AncientFoo, OldFoo)
    def foo1_migration(old):
        return OldFoo(bar=old["bar"].lower())

    @AttrsRegistry.document("Foo3")
    @attrs.define
    class Foo(chaise.dictful.Document):
        # spam is titlecase
        pass

    @AttrsRegistry.migration(OldFoo, Foo)
    def foo2_migration(old):
        return Foo(bar=old["bar"].title())

    @AttrsRegistry.document("Counter")
    @attrs.define
    class Counter(chaise.dictful.Document):
        pass

    return types.SimpleNamespace(
        Foo=Foo,
        AncientFoo=AncientFoo,
        OldFoo=OldFoo,
        Counter=Counter,
    )


@pytest.fixture
def attrs_pool(couch_url):
    return AttrsPool(couch_url)


@pytest.fixture
async def dict_session(dict_pool):
    return await dict_pool.session()


@pytest.fixture
async def dict_database(dict_session, generate_dbname):
    dbname = generate_dbname()
    db = await dict_session.create_db(dbname)
    yield db
    await dict_session.delete_db(dbname)
