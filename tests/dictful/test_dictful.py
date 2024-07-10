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

    async for doc in dict_database.mutate("test"):
        doc["spam"] = "foobar"

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
