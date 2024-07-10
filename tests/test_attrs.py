import types

import anyio
import pytest

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
    AttrsRegistry._docclasses = {}
    AttrsRegistry._migrations = []

    @AttrsRegistry.document("Foo1")
    class AncientFoo:
        # spam is uppercase
        bar: str

    @AttrsRegistry.document("Foo2")
    class OldFoo:
        # spam is lowercase
        bar: str

    @AttrsRegistry.migration(AncientFoo, OldFoo)
    def foo1_migration(old):
        return OldFoo(bar=old.bar.lower())

    @AttrsRegistry.document("Foo3")
    class Foo:
        # spam is titlecase
        spam: str

    @AttrsRegistry.migration(OldFoo, Foo)
    def foo2_migration(old):
        return Foo(spam=old.bar.title())

    @AttrsRegistry.document("Counter")
    class Counter:
        count: int

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
async def attrs_session(attrs_pool):
    return await attrs_pool.session()


@pytest.fixture
async def attrs_database(attrs_session, generate_dbname):
    dbname = generate_dbname()
    db = await attrs_session.create_db(dbname)
    yield db
    await attrs_session.delete_db(dbname)


pytestmark = pytest.mark.anyio


async def test_put(attrs_database, attrs_models):
    """
    Test that basic round-tripping works.
    """
    doc = attrs_models.Foo(spam="eggs")
    await attrs_database.attempt_put(doc, "test")

    doc2 = await attrs_database.get("test")

    assert isinstance(doc2, attrs_models.Foo)

    assert doc == doc2
    assert isinstance(doc2, attrs_models.Foo)


async def test_delete(attrs_database, attrs_models):
    """
    Test that we can delete.
    """
    doc = attrs_models.Foo(spam="eggs")
    await attrs_database.attempt_put(doc, "test")
    doc = await attrs_database.get("test")

    await attrs_database.attempt_delete(doc)

    with pytest.raises(chaise.Missing):
        await attrs_database.get("test")


async def test_simple_mutate(attrs_database, attrs_models):
    """
    Test that a trivial (non-conflicting) mutation works
    """
    doc = attrs_models.Foo(spam="eggs")
    await attrs_database.attempt_put(doc, "test")

    async for doc in attrs_database.mutate("test"):
        doc.spam = "foobar"

    doc = await attrs_database.get("test")
    assert doc.spam == "foobar"


async def test_conflicting_mutate(attrs_database, attrs_models):
    """
    Test that a conflicting mutation works
    """
    doc = attrs_models.Counter(count=0)
    await attrs_database.attempt_put(doc, "test")

    # 1. Loser gets the doc
    # 2. Winner gets and mutates the doc
    # 3. Loser mutates
    step1 = anyio.Event()
    step2 = anyio.Event()

    async def winner():
        rounds = 0
        await step1.wait()
        async for doc in attrs_database.mutate("test"):
            doc.count += 1
            rounds += 1
        step2.set()
        assert rounds == 1

    async def loser():
        rounds = 0
        async for doc in attrs_database.mutate("test"):
            step1.set()
            await step2.wait()
            doc.count += 1
            rounds += 1
        assert rounds == 2

    async with anyio.create_task_group() as tg:
        tg.start_soon(winner)
        tg.start_soon(loser)

    doc = await attrs_database.get("test")
    assert doc.count == 2


async def test_migration2(attrs_database, attrs_models):
    start = attrs_models.OldFoo(bar="spam")
    await attrs_database.attempt_put(start, "test")

    end = await attrs_database.get("test")
    assert isinstance(end, attrs_models.Foo)
    assert end.spam == "Spam"


async def test_migration3(attrs_database, attrs_models):
    start = attrs_models.AncientFoo(bar="SPAM")
    await attrs_database.attempt_put(start, "test")

    end = await attrs_database.get("test")
    assert isinstance(end, attrs_models.Foo)
    assert end.spam == "Spam"
