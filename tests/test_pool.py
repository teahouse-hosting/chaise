import pytest

import chaise
import chaise.dictful
import chaise.helpers


pytestmark = pytest.mark.anyio


class ConstantPool(chaise.helpers.ConstantPoolMixin, chaise.dictful.BasicPool):
    pass


async def test_server_fail():
    pool = ConstantPool(["http://foo:bar@nope.example", "http://foo:bar@nada.example"])

    with pytest.raises(chaise.NoServerFound):
        await pool.session()
