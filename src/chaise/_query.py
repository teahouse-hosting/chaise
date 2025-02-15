"""
Tools for munging mango queries.
"""

import copy
import types
import typing
import warnings

_UnionType = type(typing.Union[int, float])


class _BlobWalker:
    """
    Tool to walk a JSON-ish blob and munge it in place.
    """

    def __call__(self, blob):
        typ = type(blob)
        meth = getattr(self, f"walk_{typ.__name__}", None)
        if meth is None:
            warnings.warn(
                f"{type(self).__name__}: Unable to find walking method for {typ}"
            )
        else:
            meth(blob)

    def walk_str(self, val):
        pass

    def walk_int(self, val):
        pass

    def walk_float(self, val):
        pass

    def walk_bool(self, val):
        pass

    def walk_NoneType(self, val):
        pass

    def walk_tuple(self, val):
        if meth := getattr(self, "munge_tuple", None):
            meth(val)
        for item in val:
            self(item)

    def walk_list(self, val):
        if meth := getattr(self, "munge_list", None):
            meth(val)
        for item in val:
            self(item)

    def walk_dict(self, val):
        if meth := getattr(self, "munge_dict", None):
            meth(val)
        for item in val.items():
            self(item)


def _deunion(cls) -> list[type]:
    """
    Turns classes and unions into lists
    """
    if isinstance(cls, type):
        return [cls]
    elif isinstance(cls, types.UnionType):
        return list(cls.__args__)
    elif isinstance(cls, _UnionType):
        return list(cls.__args__)
    else:
        raise TypeError(f"Can't handle a class description of {cls!r}")


class _QueryMunger(_BlobWalker):
    def __init__(self, registry):
        self.registry = registry()

    def munge_dict(self, val):
        if type in val:
            classes = _deunion(val[type])
            names = []
            for cls in classes:
                names += self.registry.get_type_names(cls)

            if len(names) == 0:
                raise ValueError(f"Unable to get Database names for {val[type]!r}")
            elif len(names) == 1:
                val[self.registry.TYPE_KEY] = names[0]
            else:
                val[self.registry.TYPE_KEY] = {"$in": names}
            del val[type]


def munge_query(query: dict, registry) -> dict:
    """
    Compile out chaise's query extensions and prepare it for CouchDB.
    """
    query = copy.deepcopy(query)
    _QueryMunger(registry)(query)
    return query
