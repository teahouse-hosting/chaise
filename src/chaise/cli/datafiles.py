"""
Deals with finding and loading database/ddoc description files.
"""

import dataclasses
import importlib.resources
import posixpath
from typing import Iterable


LOADERS = {
    ".json": ...,
    ".yaml": ...,
    ".yml": ...,
    ".toml": ...,
    # '.py': ...,
}


def walk(anchor):
    """
    Generates (<path>, traversible)
    """

    def _recurse(base, trav):
        yield base, trav
        if trav.is_dir():
            for t in trav.iterdir():
                if base:
                    n = posixpath.join(base, t.name)
                else:
                    n = t.name
                yield from _recurse(n, t)

    yield from _recurse("", importlib.resources.files(anchor))


@dataclasses.dataclass
class DeclaredDB:
    name: str
    _resource: importlib.resources.abc.Traversable
    # options: ...


def find_dbs(anchor) -> Iterable[DeclaredDB]:
    for path, t in walk(anchor):
        # Traversable is a subset of pathlib.Path--it exludes most of the name
        # manipulation features
        parent, base = posixpath.split(path)
        stem, ext = posixpath.splitext(base)
        if stem == "__db__":
            try:
                LOADERS[ext]
            except KeyError as exc:
                raise Exception(f"Unable to determine loader for {path}") from exc
            # TODO: load options from file
            yield DeclaredDB(
                name=posixpath.basename(parent),
                _resource=t,
            )
