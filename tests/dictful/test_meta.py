"""
Test metadata operations
"""

import pytest


pytestmark = pytest.mark.anyio


async def test_list_dbs(basic_session, basic_database):
    all_dbs = set()
    async for dbname in basic_session.iter_dbs():
        all_dbs.add(dbname)

    assert all_dbs == {"_users", "_replicator", basic_database._name}
