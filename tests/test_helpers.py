"""
Tests for chaise.helpers
"""

from socket import AddressFamily, SocketKind

import anyio
import pytest

import chaise
import chaise.helpers


pytestmark = pytest.mark.anyio


async def test_constant_single():
    pool = chaise.helpers.ConstantPoolMixin("http://foo.bar:1234/")

    servers = set()
    async for s in pool.iter_servers():
        servers.add(s)

    assert servers == {"http://foo.bar:1234/"}


async def test_constant_multiple():
    pool = chaise.helpers.ConstantPoolMixin(
        ["http://foo.bar:1234/", "http://spam.eggs:5678/"]
    )

    servers = set()
    async for s in pool.iter_servers():
        servers.add(s)

    assert servers == {"http://foo.bar:1234/", "http://spam.eggs:5678/"}


async def test_roundrobin(monkeypatch):
    async def getaddrinfo(*p):
        # The results for google.com once
        return [
            (
                AddressFamily.AF_INET,
                SocketKind.SOCK_STREAM,
                6,
                "",
                ("142.250.191.238", 0),
            ),
            (
                AddressFamily.AF_INET,
                SocketKind.SOCK_DGRAM,
                17,
                "",
                ("142.250.191.238", 0),
            ),
            (AddressFamily.AF_INET, SocketKind.SOCK_RAW, 0, "", ("142.250.191.238", 0)),
            (
                AddressFamily.AF_INET6,
                SocketKind.SOCK_STREAM,
                6,
                "",
                ("2607:f8b0:4009:808::200e", 0, 0, 0),
            ),
            (
                AddressFamily.AF_INET6,
                SocketKind.SOCK_DGRAM,
                17,
                "",
                ("2607:f8b0:4009:808::200e", 0, 0, 0),
            ),
            (
                AddressFamily.AF_INET6,
                SocketKind.SOCK_RAW,
                0,
                "",
                ("2607:f8b0:4009:808::200e", 0, 0, 0),
            ),
            # AnyIO returns 2-tuple addresses for IPv6
            (
                AddressFamily.AF_INET6,
                SocketKind.SOCK_STREAM,
                6,
                "",
                ("fdaa:a:d05:0:1::2", 0),
            ),
            (
                AddressFamily.AF_INET6,
                SocketKind.SOCK_DGRAM,
                17,
                "",
                ("fdaa:a:d05:0:1::2", 0),
            ),
            (
                AddressFamily.AF_INET6,
                SocketKind.SOCK_RAW,
                0,
                "",
                ("fdaa:a:d05:0:1::2", 0),
            ),
        ]

    monkeypatch.setattr(anyio, "getaddrinfo", getaddrinfo)
    ...

    pool = chaise.helpers.DnsPoolMixin("http://couch.db:5984/")

    servers = set()
    async for s in pool.iter_servers():
        servers.add(s)

    assert servers == {
        "http://142.250.191.238:5984/",
        "http://[2607:f8b0:4009:808::200e]:5984/",
        "http://[fdaa:a:d05:0:1::2]:5984/",
    }
