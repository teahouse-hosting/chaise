"""
Tools for munging mango queries.
"""

import copy
import warnings


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


class _QueryMunger(_BlobWalker):
    def __init__(self, registry):
        self.registry = registry

    def munge_dict(self, val):
        if type in val:
            val[self.registry.TYPE_KEY] = ...
            del val[type]


def munge_query(query: dict, registry):
    """
    Compile out chaise's query extensions and prepare it for CouchDB.
    """
    query = copy.deepcopy(query)
    _QueryMunger(registry)(query)
    return query
