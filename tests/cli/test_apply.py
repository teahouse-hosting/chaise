import pytest


pytestmark = pytest.mark.anyio


async def test_apply(cli, cli_session):
    await cli("apply", "demo_schema")
    dbs = {db async for db in cli_session.iter_dbs() if not db.startswith("_")}
    assert dbs == {"db-empty", "db-nearly-empty", "db-realname"}

    db = await cli_session.get_db("db-realname")
    indexes = {i.name: i async for i in db.iter_indexes()}
    assert len(indexes) == 2

    assert indexes["foo"].ddoc == "a-ddoc"
    assert indexes["foo"].def_.fields == {"spam": "asc", "eggs": "asc"}
