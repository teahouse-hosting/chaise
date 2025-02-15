import enum
from typing import cast, Iterable, overload, Sequence

class EscapeMode(enum.IntFlag):
    ascii_mode = cast(int, ...)
    control = cast(int, ...)
    default = cast(int, ...)
    minimal = cast(int, ...)
    newline = cast(int, ...)
    tab = cast(int, ...)

class IdentifierMode(enum.IntFlag):
    ascii_identifiers = cast(int, ...)
    prefer_bare_identifiers = cast(int, ...)
    quote_all_identifiers = cast(int, ...)

class KdlVersion(enum.IntFlag):
    kdl_1 = cast(int, ...)
    kdl_2 = cast(int, ...)

class FloatMode:
    always_write_decimal_point: bool
    always_write_decimal_point_or_exponent: bool
    capital_e: bool
    exponent_plus: bool
    min_exponent: int
    plus: bool

    def __init__(
        self,
        *,
        always_write_decimal_point: bool | None = None,
        always_write_decimal_point_or_exponent: bool | None = None,
        capital_e: bool | None = None,
        exponent_plus: bool | None = None,
        plus: bool | None = None,
        min_exponent: int | None = None,
    ): ...

class EmitterOptions:
    escape_mode: EscapeMode
    float_mode: FloatMode
    identifier_mode: IdentifierMode
    indent: int
    version: KdlVersion
    def __init__(
        self,
        *,
        indent: int | None = None,
        escape_mode: EscapeMode | None = None,
        identifier_mode: IdentifierMode | None = None,
        float_mode: FloatMode | None = None,
        version: KdlVersion | int | None = None,
    ): ...

class ParseError(ValueError): ...
class EmitterError(RuntimeError): ...

ascii_identifiers: IdentifierMode
ascii_mode: EscapeMode
control: EscapeMode
default: EscapeMode
kdl_1: KdlVersion
kdl_2: KdlVersion
minimal: EscapeMode
newline: EscapeMode
prefer_bare_identifiers: IdentifierMode
quote_all_identifiers: IdentifierMode
tab: EscapeMode

Atomic = str | int | float | bool | None

def parse(kdl_doc: str, *, version: int | str | None = None) -> Document: ...

class Document:
    nodes: list[Node]

    def dump(self, opts: EmitterOptions | None = None): ...
    def __getitem__(self, index) -> Node: ...
    def __iter__(self) -> Iterable[Node]: ...
    def __len__(self) -> int: ...
    def __eq__(self, other: object) -> bool: ...

class Node:
    args: list[Atomic | Value]
    children: list[Node]
    name: str
    properties: dict[str, Atomic | Value]
    type_annotation: str | None

    @overload
    def __init__(self, name: str, /): ...
    @overload
    def __init__(self, type_annotation: str | None, name: str, /): ...
    @overload
    def __init__(self, name: str, /, *, properties: dict[str, Atomic | Value]): ...
    @overload
    def __init__(
        self,
        type_annotation: str | None,
        name: str,
        /,
        *,
        properties: dict[str, Atomic | Value],
    ): ...
    @overload
    def __init__(
        self,
        name: str,
        /,
        args: Sequence[Atomic | Value],
        children: Sequence[Node],
        *,
        properties: dict[str, Atomic | Value],
    ): ...
    @overload
    def __init__(
        self,
        type_annotation: str | None,
        name: str,
        /,
        args: Sequence[Atomic | Value],
        children: Sequence[Node],
        *,
        properties: dict[str, Atomic | Value],
    ): ...
    @overload
    def __init__(
        self,
        name: str,
        /,
        args: Sequence[Atomic | Value],
        children: Sequence[Node],
        **properties: Atomic | Value,
    ): ...
    @overload
    def __init__(
        self,
        type_annotation: str | None,
        name: str,
        /,
        args: Sequence[Atomic | Value],
        children: Sequence[Node],
        **properties: Atomic | Value,
    ): ...
    @overload
    def __init__(
        self,
        name: str,
        /,
        *args_and_children: Value | Atomic | Node,
        properties: dict[str, Atomic | Value],
    ): ...
    @overload
    def __init__(
        self,
        type_annotation: str | None,
        name: str,
        /,
        *args_and_children: Value | Atomic | Node,
        properties: dict[str, Atomic | Value],
    ): ...
    @overload
    def __init__(
        self,
        name: str,
        /,
        args: Sequence[Atomic | Value],
        *,
        properties: dict[str, Atomic | Value],
    ): ...
    @overload
    def __init__(
        self,
        type_annotation: str | None,
        name: str,
        /,
        args: Sequence[Atomic | Value],
        *,
        properties: dict[str, Atomic | Value],
    ): ...
    @overload
    def __init__(
        self, name: str, /, args: Sequence[Atomic | Value], **properties: Atomic | Value
    ): ...
    @overload
    def __init__(
        self,
        type_annotation: str | None,
        name: str,
        /,
        args: Sequence[Atomic | Value],
        **properties: Atomic | Value,
    ): ...
    @overload
    def __init__(
        self,
        name: str,
        /,
        *args_and_children: Value | Atomic | Node,
        **properties: Atomic | Value,
    ): ...
    @overload
    def __init__(
        self,
        type_annotation: str | None,
        name: str,
        /,
        *args_and_children: Value | Atomic | Node,
        **properties: Atomic | Value,
    ): ...
    def __eq__(self, other: object) -> bool: ...

class Value:
    type_annotation: str
    value: Atomic

    def __init__(self, type_annotation: str, value: Atomic): ...
    def __eq__(self, other: object) -> bool: ...
