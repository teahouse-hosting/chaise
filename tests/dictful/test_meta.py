"""
Test metadata operations
"""

import pytest


pytestmark = pytest.mark.anyio


async def test_list_dbs(basic_session, basic_database):
    all_dbs = set()
    async for dbname in basic_session.iter_dbs():
        if not dbname.startswith("_"):
            all_dbs.add(dbname)

    assert all_dbs == {basic_database._name}
