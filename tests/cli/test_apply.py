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

    assert indexes["bar"].ddoc == "a-ddoc"
    assert indexes["bar"].def_.fields == {"quux": "asc", "baz": "asc"}


async def test_apply_testing(couch_url, cli_session):
    import chaise.testing

    async with chaise.testing.run_cli_apply(couch_url, "demo_schema"):
        assert await cli_session.get_db("db1")
        assert await cli_session.get_db("db2")

    with pytest.raises(chaise.Missing):
        await cli_session.get_db("db1")
