"""
Integration for attrs/cattrs
"""

import typing
from typing import AbstractSet

import attrs
from cattrs.converters import Converter

try:
    # ujson is preferred, since muffin&c can also use it
    from cattrs.preconf.ujson import configure_converter
except ImportError:
    from cattrs.preconf.json import configure_converter
# Omitting orjson, even though it's a preconf, because I'm not confident it's a
# drop-in equivalent to (u)json

from . import DocumentRegistry


class classprop:
    """
    Like @property, but for class attributes
    """

    def __init__(self, factory: typing.Callable[[type], typing.Any]):
        self._factory = factory
        self.__doc__ = factory.__doc__

    def __get__(self, instance, owner):
        return self._factory(owner)

    def __set__(self, instance, value):
        raise AttributeError("Cannot set a classprop")

    def __set_name__(self, owner, name):
        self.__objclass__ = owner


class AttrsMeta(type):
    """
    Defines an attrs class as a subclass instead of a decorator
    """

    def __new__(cls, name, bases, dict, **kwds):
        sub = super().__new__(cls, name, bases, dict)
        sub = attrs.define(**kwds)(sub)
        return sub


class Document(metaclass=AttrsMeta, slots=False, frozen=False):
    __parent: typing.ClassVar[type | None] = None

    #: Document ID
    #: :meta public:
    _id: str | None = attrs.field(default=None, init=False)

    #: Document revision
    #: :meta public:
    _rev: str | None = attrs.field(default=None, init=False)

    #: Has the document been deleted? (ie, is this a tombstone?)
    #: :meta public:
    _deleted: bool = attrs.field(default=False, init=False)

    #: Attachment information, if requested
    #: :meta public:
    _attachments: dict | None = attrs.field(default=None, init=False)

    #: List of conflicts, if requested
    #: :meta public:
    _conflicts: list | None = attrs.field(default=None, init=False)

    # List of deleted conflicts, if requested
    #: :meta public:
    _deleted_conflicts: list | None = attrs.field(default=None, init=False)

    #:
    #: :meta public:
    _local_seq: str | None = attrs.field(default=None, init=False)

    #:
    #: :meta public:
    _revs_info: list | None = attrs.field(default=None, init=False)

    #:
    #: :meta public:
    _revisions: dict | None = attrs.field(default=None, init=False)

    def __init_sublcass__(cls, /, dbid: str | None = None, **kwargs):
        assert "slots" not in kwargs
        if dbid is not None and cls.__parent is not None:
            cls.__parent.document(dbid)(cls)


# All implementations exhibit the conversions:
# * bytes are wrapped in base85
# * dates & datetimes are ISO 8601
#: The converter used when talking to CouchDB.
converter = Converter(
    unstruct_collection_overrides={
        AbstractSet: list,
    }
)
configure_converter(converter)


class AttrsRegistry(DocumentRegistry):
    @classprop
    def Document(cls) -> type[Document]:
        # This is some shenanigans because names
        class Document(globals()["Document"]):
            __parent = cls

        return Document

    def load_doc(self, cls: type, blob: dict):
        return converter.structure(blob, cls)

    def dump_doc(self, doc) -> dict:
        return converter.unstructure(doc)
