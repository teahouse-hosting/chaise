"""
Various data structures used by chaise.
"""

import dataclasses
import enum
import functools

import chaise  # Be careful using this, for circular import reasons


@dataclasses.dataclass
class AllDocs_DocRef:
    """
    A document reference returned by :meth:`~chaise.Database.iter_all_docs`
    """

    #: The document ID
    docid: str

    #: The revision of the document
    rev: str

    _db: "chaise.Database"
    _doc: object | None

    async def doc(self):
        """
        Actually get the document. Since docid+rev is roughly immutable, caches
        it.

        (Might be pre-loaded by the producing function.)
        """
        if self._doc is None:
            # docid + revision is immutable(ish), so it's safe to cache
            # (It can still be deleted/vacuumed, but that's fine. probably.)
            self._doc = await self._db.get(self.docid, rev=self.rev)
        return self._doc


class AscDesc(enum.StrEnum):
    ASC = "asc"
    DESC = "desc"


@dataclasses.dataclass
class IndexDef:
    """
    Index Definition.
    """

    #: Fields and their direction.
    fields: dict[str, AscDesc]


@dataclasses.dataclass
class Index:
    """
    Return of :meth:`~chaise.Database.iter_indexes`
    """

    #: ID of the design document the index belongs to.
    ddoc: str
    #: Name of the index.
    name: str
    #: Partitioned (:const:`True`) or global (:const:`False`) index.
    partitioned: bool
    #: Type of the index. Currently ``"json"`` is the only supported type.
    type: str
    #: Definition of the index, containing the indexed fields and the sort
    #: order: ascending or descending.
    def_: IndexDef

    @classmethod
    def from_dict(cls, data):
        return cls(
            ddoc=data["ddoc"],
            name=data["name"],
            partitioned=data["partitioned"],
            type=data["type"],
            def_=IndexDef(
                fields={
                    k: AscDesc(v)
                    for k, v in functools.reduce(
                        dict.update, data["def"]["fields"], {}
                    ).items()
                },
            ),
        )
