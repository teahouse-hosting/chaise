from typing import AsyncIterator

import httpx


class CouchSession:
    """
    A connection to CouchDB.
    """

    _client: httpx.AsyncClient
    _root: httpx.URL

    def __init__(self, client: httpx.AsyncClient, root: httpx.URL):
        self._client = client
        self._root = root

    def get_doc(
        self,
        db: str,
        docid: str,
        *,
        attachments: bool = False,
        conflicts: bool = False,
        deleted_conflicts: bool = False,
        latest: bool = False,
        local_seq: bool = False,
        meta: bool = False,
        open_revs: list[str] | None = None,
        rev: str | None = None,
        revs: bool = False,
        revs_info: bool = False,
    ):
        """
        Get a document

        https://docs.couchdb.org/en/stable/api/document/common.html#get--db-docid
        """

    def attempt_put_doc(self, doc, *, batch: bool = False):
        """
        Update a document

        https://docs.couchdb.org/en/stable/api/document/common.html#put--db-docid
        """

    def attempt_delete_doc(self, doc, *, batch: bool = False):
        """
        Delete a document

        https://docs.couchdb.org/en/stable/api/document/common.html#delete--db-docid
        """

    def attempt_copy_doc(self, src_doc, dst_doc, *, batch: bool = False):
        """
        Copy a document

        https://docs.couchdb.org/en/stable/api/document/common.html#copy--db-docid
        """

    # TODO: Mango searches
    # TODO: Database operations


class SessionPool:
    """
    Responsible for giving out Couch connections
    """

    _client: httpx.AsyncClient

    #: Class to use for sessions
    session_class: type[CouchSession]

    def __init__(self):
        super().__init__()
        self._client = self.make_client()

    def make_client(self) -> httpx.AsyncClient:
        """
        Produce an httpx client.
        """
        return httpx.AsyncClient(http2=True, follow_redirects=True)

    async def iter_servers(self) -> AsyncIterator[str]:
        """
        Produce the list of potential servers.

        Override this
        """
        raise NotImplementedError
        yield from ()

    async def _check_server(self, url: httpx.URL):
        resp = await self._client.get(url.join("_up"))
        return resp.is_success

    async def session(self) -> CouchSession:
        """
        Get a session
        """
        async for url in self.iter_servers():
            url = httpx.URL(url)
            if await self._check_server(url):
                return self.session_class(self._client, url)
