"""
Tests for chaise.dictful.Basic* versions of things.
"""

import anyio
import pytest

import chaise
from chaise.dictful import Document


pytestmark = pytest.mark.anyio


async def test_put(basic_pool, basic_database):
    """
    Test that basic round-tripping works.
    """
    session = await basic_pool.session()
    doc = Document(spam="eggs")
    await session.attempt_put_doc(doc, basic_database, "test")

    doc2 = await session.get_doc(basic_database, "test")

    assert dict(doc) == dict(doc2)


async def test_delete(basic_pool, basic_database):
    """
    Test that we can delete.
    """
    session = await basic_pool.session()
    doc = Document(spam="eggs")
    await session.attempt_put_doc(doc, basic_database, "test")
    doc = await session.get_doc(basic_database, "test")

    await session.attempt_delete_doc(doc)
    with pytest.raises(chaise.Missing):
        await session.get_doc(basic_database, "test")


async def test_simple_mutate(basic_pool, basic_database):
    """
    Test that a trivial (non-conflicting) mutation works
    """
    session = await basic_pool.session()
    doc = Document(spam="eggs")
    await session.attempt_put_doc(doc, basic_database, "test")

    async for doc in session.mutate_doc(basic_database, "test"):
        doc["spam"] = "foobar"

    doc = await session.get_doc(basic_database, "test")
    assert doc["spam"] == "foobar"


async def test_conflicting_mutate(basic_pool, basic_database):
    """
    Test that a conflicting mutation works
    """
    session = await basic_pool.session()
    doc = Document(count=0)
    await session.attempt_put_doc(doc, basic_database, "test")

    # 1. Loser gets the doc
    # 2. Winner gets and mutates the doc
    # 3. Loser mutates
    step1 = anyio.Event()
    step2 = anyio.Event()

    async def winner():
        rounds = 0
        await step1.wait()
        async for doc in session.mutate_doc(basic_database, "test"):
            doc["count"] += 1
            rounds += 1
        step2.set()
        assert rounds == 1

    async def loser():
        rounds = 0
        async for doc in session.mutate_doc(basic_database, "test"):
            step1.set()
            await step2.wait()
            doc["count"] += 1
            rounds += 1
        assert rounds == 2

    async with anyio.create_task_group() as tg:
        tg.start_soon(winner)
        tg.start_soon(loser)

    doc = await session.get_doc(basic_database, "test")
    assert doc["count"] == 2
