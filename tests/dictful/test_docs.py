import pytest

from chaise.dictful import Document


pytestmark = pytest.mark.anyio


async def test_basic_put(basic_pool, basic_database):
    """
    Test that basic round-tripping works.
    """
    session = await basic_pool.session()
    doc = Document(spam="eggs")
    await session.attempt_put_doc(doc, basic_database, "test")

    doc2 = await session.get_doc(basic_database, "test")

    assert dict(doc) == dict(doc2)
