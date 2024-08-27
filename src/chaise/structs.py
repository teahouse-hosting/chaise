"""
Various data structures used by chaise.
"""

import dataclasses

import chaise  # Be careful using this, for circular import reasons


@dataclasses.dataclass
class AllDocs_DocRef:
    docid: str
    rev: str
    _db: "chaise.Database"
    _doc: object | None

    async def doc(self):
        if self._doc is None:
            # docid + revision is immutable(ish), so it's safe to cache
            # (It can still be deleted/vacuumed, but that's fine. probably.)
            self._doc = await self._db.get(self.docid, rev=self.rev)
        return self._doc
