"""
Tests for chaise.dictful.Basic* versions of things.
"""

import anyio
import pytest

import chaise


pytestmark = pytest.mark.anyio


async def test_put(dict_database, dict_models):
    """
    Test that basic round-tripping works.
    """
    doc = dict_models.Foo(spam="eggs")
    await dict_database.attempt_put(doc, "test")
    assert doc.id == "test"
    assert doc.rev

    doc2 = await dict_database.get("test")

    assert isinstance(doc2, dict_models.Foo)
    assert dict(doc) == dict(doc2)
    assert isinstance(doc2, dict_models.Foo)


async def test_delete(dict_database, dict_models):
    """
    Test that we can delete.
    """
    doc = dict_models.Foo(spam="eggs")
    await dict_database.attempt_put(doc, "test")
    doc = await dict_database.get("test")

    await dict_database.attempt_delete(doc)

    with pytest.raises(chaise.Missing):
        await dict_database.get("test")


async def test_simple_mutate(dict_database, dict_models):
    """
    Test that a trivial (non-conflicting) mutation works
    """
    doc = dict_models.Foo(spam="eggs")
    await dict_database.attempt_put(doc, "test")
    r1 = doc.rev

    async for doc in dict_database.mutate("test"):
        doc["spam"] = "foobar"

    assert doc.rev != r1

    doc = await dict_database.get("test")
    assert doc["spam"] == "foobar"


async def test_conflicting_mutate(dict_database, dict_models):
    """
    Test that a conflicting mutation works
    """
    doc = dict_models.Counter(count=0)
    await dict_database.attempt_put(doc, "test")

    # 1. Loser gets the doc
    # 2. Winner gets and mutates the doc
    # 3. Loser mutates
    step1 = anyio.Event()
    step2 = anyio.Event()

    async def winner():
        rounds = 0
        await step1.wait()
        async for doc in dict_database.mutate("test"):
            doc["count"] += 1
            rounds += 1
        step2.set()
        assert rounds == 1

    async def loser():
        rounds = 0
        async for doc in dict_database.mutate("test"):
            step1.set()
            await step2.wait()
            doc["count"] += 1
            rounds += 1
        assert rounds == 2

    async with anyio.create_task_group() as tg:
        tg.start_soon(winner)
        tg.start_soon(loser)

    doc = await dict_database.get("test")
    assert doc["count"] == 2


async def test_migration2(dict_database, dict_models):
    start = dict_models.OldFoo(bar="spam")
    await dict_database.attempt_put(start, "test")

    end = await dict_database.get("test")
    assert isinstance(end, dict_models.Foo)
    assert end["bar"] == "Spam"


async def test_migration3(dict_database, dict_models):
    start = dict_models.AncientFoo(bar="SPAM")
    await dict_database.attempt_put(start, "test")

    end = await dict_database.get("test")
    assert isinstance(end, dict_models.Foo)
    assert end["bar"] == "Spam"


async def test_all_docs_design(dict_database, dict_models):
    """
    Test that iter_all_docs skips design documents
    """
    # Skip document handling to insert raw design document
    await dict_database._session._request(
        "PUT",
        dict_database._name,
        "_design/spam",
        json={},
    )

    doc = dict_models.Foo(spam="eggs")
    await dict_database.attempt_put(doc, "test")

    all_docs = [ref async for ref in dict_database.iter_all_docs()]

    assert len(all_docs) == 1


async def test_type_munge_single(dict_session, dict_models):
    registry = dict_session.loader
    from chaise._query import munge_query

    assert munge_query({type: dict_models.Counter, "foo": "bar"}, registry) == {
        registry.TYPE_KEY: "Counter",
        "foo": "bar",
    }


async def test_type_munge_migrations(dict_session, dict_models):
    registry = dict_session.loader
    from chaise._query import munge_query

    assert munge_query({type: dict_models.Foo}, registry) == {
        registry.TYPE_KEY: {"$in": ["Foo3", "Foo2", "Foo1"]}
    }


async def test_type_munge_union(dict_session, dict_models):
    registry = dict_session.loader
    from chaise._query import munge_query

    assert munge_query({type: dict_models.Counter | dict_models.Foo}, registry) == {
        registry.TYPE_KEY: {"$in": ["Counter", "Foo3", "Foo2", "Foo1"]}
    }


async def test_find_type(dict_database, dict_models):
    doc = dict_models.Counter(count=0)
    await dict_database.attempt_put(doc, "test")
    doc1 = dict_models.AncientFoo(bar="SPAM")
    doc2 = dict_models.OldFoo(bar="spam")
    doc3 = dict_models.Foo(spam="eggs")
    await dict_database.attempt_put(doc1, "test1")
    await dict_database.attempt_put(doc2, "test2")
    await dict_database.attempt_put(doc3, "test3")

    docs = [doc async for doc in dict_database.find({type: dict_models.Counter})]

    assert len(docs) == 1


async def test_find_migrations(dict_database, dict_models):
    doc = dict_models.Counter(count=0)
    await dict_database.attempt_put(doc, "test")
    doc1 = dict_models.AncientFoo(bar="SPAM")
    doc2 = dict_models.OldFoo(bar="spam")
    doc3 = dict_models.Foo(spam="eggs")
    await dict_database.attempt_put(doc1, "test1")
    await dict_database.attempt_put(doc2, "test2")
    await dict_database.attempt_put(doc3, "test3")

    docs = [doc async for doc in dict_database.find({type: dict_models.Foo})]

    assert len(docs) == 3
    assert all(isinstance(d, dict_models.Foo) for d in docs)


async def test_type_migratios(dict_database, dict_models):
    # Low-level put to force the old type key
    resp = await dict_database._session._request(
        "PUT",
        dict_database._name,
        "test",
        json={"": "Counter"},
    )
    payload = resp.json()
    assert payload["ok"]

    doc = await dict_database.get("test")
    assert isinstance(doc, dict_models.Counter)
