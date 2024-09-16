"""
Extra bits to make your job easier.
"""

import random
from socket import AddressFamily, SocketKind


import anyio
import httpx

from . import SessionPool


class ConstantPoolMixin(SessionPool):
    """
    A trivial pool mixin that uses the passed in URL(s).
    """

    urls: list[str]

    def __init__(self, urls: str | list[str]):
        if isinstance(urls, str):
            self.urls = [urls]
        else:
            self.urls = list(urls)
        super().__init__()

    async def iter_servers(self):
        u = self.urls[:]
        random.shuffle(u)
        for url in u:
            yield url


async def _get_ips(hostname: str | bytes, port: int | None = None):
    """
    Look up the IPs for a given hostname
    """
    for gai in await anyio.getaddrinfo(hostname, port):
        match gai:
            case (AddressFamily.AF_INET, SocketKind.SOCK_STREAM, _, _, (addr, _)):
                yield addr
            case (
                AddressFamily.AF_INET6,
                SocketKind.SOCK_STREAM,
                _,
                _,
                (addr, _),
            ):
                yield addr
            case (
                AddressFamily.AF_INET6,
                SocketKind.SOCK_STREAM,
                _,
                _,
                (addr, _, _, scope),
            ):
                # IPv6 flow is without purpose and cannot be represented in addresses
                if scope:
                    yield f"{addr}%{scope}"
                else:
                    yield addr
            case _:
                continue


class DnsPoolMixin(SessionPool):
    """
    Uses DNS round robin to find pool members.

    Assumes that CouchDB is not behind a vhost or uses TLS.
    """

    url: httpx.URL

    def __init__(self, url: str):
        self.url = httpx.URL(url)
        super().__init__()

    async def iter_servers(self):
        # The domain stack already does our shuffling
        async for ip in _get_ips(self.url.raw_host, self.url.port):
            if ":" in ip:
                ip = f"[{ip}]"
            yield str(self.url.copy_with(host=ip))
