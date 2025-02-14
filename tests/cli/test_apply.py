import pytest


pytestmark = pytest.mark.anyio


async def test_apply(cli, cli_session):
    await cli("apply", "demo_schema")
    assert await cli_session.get_db("db1")
    assert await cli_session.get_db("db2")


async def test_apply_testing(couch_url, cli_session):
    import chaise.testing

    async with chaise.testing.run_cli_apply(couch_url, "demo_schema"):
        assert await cli_session.get_db("db1")
        assert await cli_session.get_db("db2")

    with pytest.raises(chaise.Missing):
        await cli_session.get_db("db1")
