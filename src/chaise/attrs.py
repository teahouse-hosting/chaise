"""
Integration for attrs/cattrs
"""

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


# All implementations exhibit the conversions:
# * bytes are wrapped in base85
# * dates & datetimes are ISO 8601
converter = Converter(
    unstruct_collection_overrides={
        AbstractSet: list,
    }
)
configure_converter(converter)


class AttrsRegistry(DocumentRegistry):
    @classmethod
    def document(cls, name: str, /, **flags):
        """
        Registers a class as a document of the given type.

        Passes it through :func:`attrs.define`
        """
        func = super().document(name)

        def _(klass: type):
            # Disable slots so chaise can attach extra data
            klass = attrs.mutable(klass, slots=False, **flags)
            return func(klass)

        return _

    def load_doc(self, cls: type, blob: dict):
        return converter.structure(blob, cls)

    def dump_doc(self, doc) -> dict:
        return converter.unstructure(doc)
