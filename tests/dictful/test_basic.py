"""
Tests for chaise.dictful.Basic* versions of things.
"""

import anyio
import pytest

import chaise
from chaise.dictful import Document


pytestmark = pytest.mark.anyio


async def test_put(basic_database):
    """
    Test that basic round-tripping works.
    """
    doc = Document(spam="eggs")
    await basic_database.attempt_put(doc, "test")

    doc2 = await basic_database.get("test")

    assert dict(doc) == dict(doc2)


async def test_delete(basic_database):
    """
    Test that we can delete.
    """
    doc = Document(spam="eggs")
    await basic_database.attempt_put(doc, "test")
    doc = await basic_database.get("test")

    await basic_database.attempt_delete(doc)

    with pytest.raises(chaise.Missing):
        await basic_database.get("test")


async def test_simple_mutate(basic_database):
    """
    Test that a trivial (non-conflicting) mutation works
    """
    doc = Document(spam="eggs")
    await basic_database.attempt_put(doc, "test")

    async for doc in basic_database.mutate("test"):
        doc["spam"] = "foobar"

    doc = await basic_database.get("test")
    assert doc["spam"] == "foobar"


async def test_conflicting_mutate(basic_database):
    """
    Test that a conflicting mutation works
    """
    doc = Document(count=0)
    await basic_database.attempt_put(doc, "test")

    # 1. Loser gets the doc
    # 2. Winner gets and mutates the doc
    # 3. Loser mutates
    step1 = anyio.Event()
    step2 = anyio.Event()

    async def winner():
        rounds = 0
        await step1.wait()
        async for doc in basic_database.mutate("test"):
            doc["count"] += 1
            rounds += 1
        step2.set()
        assert rounds == 1

    async def loser():
        rounds = 0
        async for doc in basic_database.mutate("test"):
            step1.set()
            await step2.wait()
            doc["count"] += 1
            rounds += 1
        assert rounds == 2

    async with anyio.create_task_group() as tg:
        tg.start_soon(winner)
        tg.start_soon(loser)

    doc = await basic_database.get("test")
    assert doc["count"] == 2


async def test_all_docs(basic_database):
    """
    Test that we can get all docs
    """
    doc = Document(spam="eggs")
    await basic_database.attempt_put(doc, "test")

    all_docs = []
    async for ref in basic_database.iter_all_docs():
        all_docs.append(ref)

    assert len(all_docs) == 1
    assert ref.docid == "test"
    assert await ref.doc() == doc


async def test_all_docs_include(basic_database):
    """
    Test that we can get all docs, and include the docs
    """
    doc = Document(spam="eggs")
    await basic_database.attempt_put(doc, "test")

    all_docs = []
    async for ref in basic_database.iter_all_docs(include_docs=True):
        all_docs.append(ref)

    assert len(all_docs) == 1
    assert ref.docid == "test"
    assert ref._doc is not None
    assert await ref.doc() == doc
