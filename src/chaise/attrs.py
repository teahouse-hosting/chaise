"""
Integration for attrs/cattrs
"""

import typing
from typing import AbstractSet
import warnings

import attrs
import cattrs.converters
import cattrs.gen

try:
    # ujson is preferred, since muffin&c can also use it
    from cattrs.preconf.ujson import configure_converter
except ImportError:
    from cattrs.preconf.json import configure_converter
# Omitting orjson, even though it's a preconf, because I'm not confident it's a
# drop-in equivalent to (u)json

from . import DocumentRegistry


# All implementations exhibit the conversions:
# * bytes are wrapped in base85
# * dates & datetimes are ISO 8601
#: The converter used when talking to CouchDB.
converter = cattrs.converters.Converter(
    unstruct_collection_overrides={
        AbstractSet: list,
    }
)
configure_converter(converter)


class classprop:
    """
    Like @property, but for class attributes

    :meta private:
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


class DocMeta(type):
    """
    Defines an attrs class as a subclass instead of a decorator

    :meta private:
    """

    def __new__(cls, name, bases, dict, **kwds):
        sub = super().__new__(cls, name, bases, dict)
        dbid = kwds.pop("dbid", None)
        assert not kwds.get("slots", None)
        if "__attrs_attrs__" not in dict:  # prevents recursion
            sub = attrs.define(**kwds)(sub)

            # Register the class with chaise
            if sub.__module__ != globals()["__name__"] and dbid is None:
                warnings.warn(f"No dbid given for {sub!r}")
            if dbid is not None and sub._Document__parent is not None:
                sub._Document__parent.document(dbid)(sub)

            # Register the class with cattrs
            converter.register_unstructure_hook(
                sub,
                cattrs.gen.make_dict_unstructure_fn(
                    sub,
                    converter,
                    _id=cattrs.gen.override(omit=True),
                    _rev=cattrs.gen.override(omit=True),
                    _deleted=cattrs.gen.override(omit_if_default=True),
                    _attachments=cattrs.gen.override(omit=True),
                    _conflicts=cattrs.gen.override(omit=True),
                    _deleted_conflicts=cattrs.gen.override(omit=True),
                    _local_seq=cattrs.gen.override(omit=True),
                    _revs_info=cattrs.gen.override(omit=True),
                    _revisions=cattrs.gen.override(omit=True),
                ),
            )
        return sub


class Document(metaclass=DocMeta, slots=False, frozen=False):
    """
    The parent class for all documents that get saved to Couch.

    Do not inherit from directly; use :class:`AttrsRegistry.Document` instead.
    """

    __parent: typing.ClassVar[type | None] = None

    #: Document ID
    #:
    #: :meta public:
    _id: str | None = attrs.field(default=None, kw_only=True, alias="_id")

    #: Document revision
    #:
    #: :meta public:
    _rev: str | None = attrs.field(default=None, kw_only=True, alias="_rev")

    #: Has the document been deleted? (ie, is this a tombstone?)
    #:
    #: :meta public:
    _deleted: bool = attrs.field(default=False, kw_only=True, alias="_deleted")

    #: Attachment information, if requested
    #:
    #: :meta public:
    _attachments: dict | None = attrs.field(
        default=None, kw_only=True, alias="_attachments"
    )

    #: List of alternate document versions, if requested
    #:
    #: :meta public:
    _conflicts: list | None = attrs.field(
        default=None, kw_only=True, alias="_conflicts"
    )

    #: List of deleted conflicts, if requested
    #:
    #: :meta public:
    _deleted_conflicts: list | None = attrs.field(
        default=None, kw_only=True, alias="_deleted_conflicts"
    )

    #:
    #: :meta public:
    _local_seq: str | None = attrs.field(default=None, kw_only=True, alias="_local_seq")

    #:
    #: :meta public:
    _revs_info: list | None = attrs.field(
        default=None, kw_only=True, alias="_revs_info"
    )

    #:
    #: :meta public:
    _revisions: dict | None = attrs.field(
        default=None, kw_only=True, alias="_revisions"
    )


class AttrsRegistry(DocumentRegistry):
    @classprop
    def Document(cls) -> type[Document]:
        """
        Document superclass.

        Handles:

        * Making an attrs
        * Registering with chaise
        * Serialization concerns

        Me sure to include the ``dbid`` keyword argument::

           class MyDoc(AttrsRegistry.Document, dbid="mydoc"): ...
        """

        # This is some shenanigans because names
        class Document(globals()["Document"]):
            __doc__ = vars(AttrsRegistry)["Document"].__doc__
            __parent = cls

        return Document

    def load_doc(self, cls: type, blob: dict):
        """
        :meta private:
        """
        return converter.structure(blob, cls)

    def dump_doc(self, doc) -> dict:
        """
        :meta private:
        """
        return converter.unstructure(doc)
