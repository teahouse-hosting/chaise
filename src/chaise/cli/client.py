import chaise.dictful


class ConstantPool(chaise.dictful.BasicPool):
    def __init__(self, url: str):
        self.url = url
        super().__init__()

    async def iter_servers(self):
        yield self.url
