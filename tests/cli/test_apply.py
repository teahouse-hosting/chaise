import pytest


pytestmark = pytest.mark.anyio


async def test_apply(cli, cli_session):
    await cli("apply", "demo_schema")
    dbs = {db async for db in cli_session.iter_dbs() if not db.startswith("_")}
    assert dbs == {"db-empty", "db-nearly-empty", "db-realname"}
