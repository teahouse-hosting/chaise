import types

import anyio
import pytest

import chaise
import chaise.attrs
import chaise.helpers


class AttrsRegistry(chaise.attrs.AttrsRegistry):
    pass


class AttrsSession(chaise.CouchSession):
    loader = AttrsRegistry


class AttrsPool(chaise.helpers.ConstantPoolMixin, chaise.SessionPool):
    session_class = AttrsSession


@pytest.fixture(scope="session")
def attrs_models():
    AttrsRegistry._docclasses = {}
    AttrsRegistry._migrations = []

    class AncientFoo(AttrsRegistry.Document, dbid="Foo1"):
        # spam is uppercase
        bar: str

    class OldFoo(AttrsRegistry.Document, dbid="Foo2"):
        # spam is lowercase
        bar: str

    @AttrsRegistry.migration(AncientFoo, OldFoo)
    def foo1_migration(old):
        return OldFoo(bar=old.bar.lower())

    class Foo(AttrsRegistry.Document, dbid="Foo3"):
        # spam is titlecase
        spam: str

    @AttrsRegistry.migration(OldFoo, Foo)
    def foo2_migration(old):
        return Foo(spam=old.bar.title())

    class Counter(AttrsRegistry.Document, dbid="Counter"):
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


async def test_unstruct(attrs_session, attrs_models):
    """
    Tests that the data we send to CouchDB is what we expect
    """
    doc = attrs_models.Foo(spam="eggs", _id="test")
    blob = attrs_session.loader().dump_to_blob(doc)

    assert blob == {"": "Foo3", "spam": "eggs"}


async def test_struct(attrs_session, attrs_models):
    """
    Tests that the data we can handle data we expect from CouchDB
    """
    blob = {"_id": "test", "": "Foo3", "spam": "eggs"}
    doc = attrs_session.loader().load_from_blob(blob)

    assert isinstance(doc, attrs_models.Foo)
    assert doc.spam == "eggs"
    assert doc._id == "test"


async def test_put(attrs_database, attrs_models):
    """
    Test that basic round-tripping works.
    """
    doc = attrs_models.Foo(spam="eggs")
    await attrs_database.attempt_put(doc, "test")

    doc2 = await attrs_database.get("test")

    assert isinstance(doc2, attrs_models.Foo)

    # Requires https://github.com/teahouse-hosting/chaise/issues/1
    # assert doc == doc2
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


async def test_metadata(attrs_database, attrs_models):
    """
    Test that metadata attributes are what we'd expect
    """
    doc = attrs_models.Foo(spam="eggs")
    await attrs_database.attempt_put(doc, "test")

    doc2 = await attrs_database.get("test", attachments=True, conflicts=True, revs=True)

    assert isinstance(doc2, attrs_models.Foo)

    assert doc2._id == "test"
    assert doc2._rev
    assert doc2._attachments == {}
    assert doc2._conflicts == []
    assert doc2._revisions
