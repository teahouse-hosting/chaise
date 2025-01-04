"""
Deals with finding and loading database/ddoc description files.
"""

import dataclasses
import importlib.resources
import posixpath
from typing import Iterable

import ckdl


class ParseError(Exception):
    pass


@dataclasses.dataclass
class Index:
    name: str
    fields: list[str]
    filter: dict | None = None


@dataclasses.dataclass
class DesignDoc:
    name: str
    _resource: importlib.resources.abc.Traversable
    indexes: list[Index]


@dataclasses.dataclass
class DeclaredDB:
    name: str
    _resource: importlib.resources.abc.Traversable
    # options: ...
    ddocs: list[DesignDoc]


class Loader:
    def load_database(self, file_contents: str, db: DeclaredDB):
        raise NotImplementedError

    def load_ddoc(self, file_contents: str, ddoc: DesignDoc):
        raise NotImplementedError


class KdlLoader:
    def load_database(self, file_contents: str, db: DeclaredDB):
        if not file_contents.strip():
            return
        doc = ckdl.parse(file_contents, version="detect")
        assert len(doc.nodes) == 1
        (node,) = doc.nodes
        assert node.name == "database"
        assert not node.children
        match node.args:
            case ():
                pass
            case (name,):
                db.name = name
            case _:
                raise ParseError(f"Invalid KDL: Unexpected arguments: {node}")

    def load_ddoc(self, file_contents: str, ddoc: DesignDoc):
        if not file_contents.strip():
            return
        doc = ckdl.parse(file_contents, version="detect")

        for node in doc.nodes:
            match node.name:
                case "index":
                    ddoc.indexes.append(self._parse_index(node))
                case _:
                    raise ParseError(f"Uknown node: {node}")

    def _parse_index(self, node) -> Index:
        match node.args:
            case ():
                raise ParseError(f"Invalid KDL: Expecting arguments: {node}")
            case (name,):
                index_name = name
            case _:
                raise ParseError(f"Invalid KDL: Unexpected arguments: {node}")

        index_fields = []
        for child in node.children:
            match child.name:
                case "field" | "fields":
                    index_fields += child.args
                case _:
                    raise ParseError(f"Invalid KDL: Uknown node: {child}")

        return Index(
            name=index_name,
            fields=index_fields,
        )


LOADERS: dict[str, type[Loader]] = {
    ".kdl": KdlLoader,
    # ".json": ...,
    # ".yaml": ...,
    # ".yml": ...,
    # ".toml": ...,
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
                if not hasattr(t, "parent"):
                    t.parent = trav
                yield from _recurse(n, t)

    yield from _recurse("", importlib.resources.files(anchor))


def find_dbs(anchor) -> Iterable[DeclaredDB]:
    for path, t in walk(anchor):
        # Traversable is a subset of pathlib.Path--it exludes most of the name
        # manipulation features
        parent, base = posixpath.split(path)
        stem, ext = posixpath.splitext(base)
        if stem == "__db__":
            try:
                loader = LOADERS[ext]()
            except KeyError as exc:
                raise Exception(f"Unable to determine loader for {path}") from exc
            else:
                obj = DeclaredDB(
                    name=posixpath.basename(parent),
                    _resource=t,
                    ddocs=[],
                )
                loader.load_database(t.read_text(), obj)
                obj.ddocs += list(find_ddocs(t.parent))
                yield obj


def find_ddocs(trav):
    assert trav.is_dir()
    for file in trav.iterdir():
        if file.is_dir():
            continue
        stem, ext = posixpath.splitext(file.name)
        if stem == "__db__":
            continue
        try:
            loader = LOADERS[ext]()
        except KeyError as exc:
            # TODO: emit warning
            exc
        else:
            ddoc = DesignDoc(
                name=stem,
                _resource=file,
                indexes=[],
            )
            loader.load_ddoc(file.read_text(), ddoc)
            yield ddoc
