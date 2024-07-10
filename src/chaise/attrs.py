"""
Integration for attrs/cattrs
"""

from typing import AbstractSet

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
    def load_doc(self, cls: type, blob: dict):
        return converter.structure(blob, cls)

    def dump_doc(self, doc) -> dict:
        return converter.unstructure(doc)
