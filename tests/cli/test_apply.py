import pytest


pytestmark = pytest.mark.anyio


async def test_apply(cli, cli_session):
    await cli("apply", "demo_schema")
    assert await cli_session.get_db("db1")
    assert await cli_session.get_db("db2")
