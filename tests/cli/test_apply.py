import pytest


pytestmark = pytest.mark.anyio


async def test_apply(cli):
    await cli("apply", "demo_schema")
