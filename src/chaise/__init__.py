from typing import AsyncIterator, Literal

import httpx


class Conflict(Exception):
    """
    There was a conflict when trying to perform the operation.
    """


class Missing(Exception):
    """
    Could not find the requested document
    """


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
        open_revs: list[str] | Literal["all"] | None = None,
        rev: str | None = None,
        revs: bool = False,
        revs_info: bool = False,
    ):
        """
        Get a document

        https://docs.couchdb.org/en/stable/api/document/common.html#get--db-docid
        """
        resp = await self._client.get(
            self._root.join(db, docid),
            params={
                "attachments": attachments,
                "conflicts": conflicts,
                "deleted_conflicts": deleted_conflicts,
                "latest": latest,
                "local_seq": local_seq,
                "meta": meta,
                "open_revs": open_revs,
                "rev": rev,
                "revs": revs,
                "revs_info": revs_info,
            },
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            match exc.response.status_code:
                case 404:
                    raise Missing(f"Could not find {docid!r} in {db!r}") from exc
                case 409:
                    raise Conflict(f"Conflict updating {docid!r} in {db!r}") from exc
                case _:
                    raise

        blob = resp.json()
        doc = blob  # FIXME: parse into a document
        return doc

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

    async def mutate_doc(self, db: str, docid: str) -> AsyncIterator:
        """
        A document mutation loop::

            async for doc in couch.mutate_doc("spam", "eggs"):
                doc.foo = "bar"

        Will replay the mutation until it goes through.
        """
        doc = await self.get_doc(db, docid)
        yield doc
        while True:
            try:
                await self.attempt_put_doc(doc)
            except Conflict:
                doc = await self.get_doc(db, docid)
            else:
                break

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
