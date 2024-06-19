import json
from typing import AsyncIterator, Literal, Callable, Protocol, TypeVar, Generic

import httpx


DOCT = TypeVar("DOCT")


class DocumentLoader(Protocol, Generic[DOCT]):
    def loadj(self, blob: dict) -> DOCT:
        """
        Convert a JSON blob into a document object.
        """

    def dumpj(self, doc: DOCT) -> dict:
        """
        Convert a document into a JSON blob.
        """


class DocumentRegistry:
    """
    Handles de/serialization, manages migrations, etc.

    Default loader implementation.

    Must subclass.
    """

    TYPE_KEY = ""

    @classmethod
    def document(cls, name: str):
        """
        Register a class as a loadable couch document.
        """

        def _(klass: type):
            return klass

        return _

    @classmethod
    def migration(cls, before: type, after: type):
        """
        Define a function that'll convert between documents.
        """

        def _(func: Callable):
            return func

        return _

    def load_doc(self, cls: type, blob: dict):
        """
        Converts a JSON blob into a document.

        Override me.
        """
        raise NotImplementedError

    def dump_doc(self, doc) -> dict:
        """
        Convert a document into a JSON blob.

        Override me.
        """
        raise NotImplementedError

    def loadj(self, blob):
        type = blob.pop(self.TYPE_KEY)
        klass = ...(type)  # TODO: find class from type
        doc = self.load_doc(klass, blob)
        # TODO: Migrations
        return doc

    def dumpj(self, doc):
        blob = self.dump_doc(doc)
        blob[self.TYPE_KEY] = ...  # TODO: Find type from class
        return blob


class Conflict(Exception):
    """
    There was a conflict when trying to perform the operation.
    """


class Missing(Exception):
    """
    Could not find the requested document.

    Note that this is a 404, not a tombstone.
    """


class Deleted(Exception):
    """
    Requested a deleted document.

    Note that this is a document with a tombstone, not a 404.
    """


class CouchSession:
    """
    A connection to CouchDB.
    """

    _client: httpx.AsyncClient
    _root: httpx.URL

    loader: type[DocumentLoader]

    def __init__(self, client: httpx.AsyncClient, root: httpx.URL):
        self._client = client
        self._root = root

    @staticmethod
    def _fix_params(params):
        rv = {}
        for key, value in params.items():
            if value is None:
                continue
            else:
                rv[key] = json.dumps(value)
        return rv

    async def _request(self, method, *urlparts, **kwargs):
        url = self._root.join("/".join(urlparts))
        if "params" in kwargs:
            kwargs["params"] = self._fix_params(kwargs["params"])
        resp = await self._client.request(method, url, **kwargs)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            exc.add_note(f"Body: {exc.response.text}")
            match exc.response.status_code:
                case 404:
                    raise Missing(f"Could not find {'/'.join(urlparts)}") from exc
                case 409:
                    raise Conflict(f"Conflict updating {'/'.join(urlparts)}") from exc
                case _:
                    raise
        return resp

    def _blob2doc(self, blob, db, docid, etag):
        doc = self.loader().loadj(blob)
        doc.__db = db
        doc.__docid = docid
        doc.__etag = etag
        return doc

    def _doc2blob(self, doc):
        blob = self.loader().dumpj(doc)
        db = docid = etag = None
        try:
            db = doc.__db
            docid = doc.__docid
            etag = doc.__etag
        except AttributeError:
            pass
        return blob, db, docid, etag

    async def get_doc(
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
        resp = await self._request(
            "GET",
            db,
            docid,
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
            headers={
                "Accept": "application/json",
            },
        )

        blob = resp.json()
        if blob.get("_deleted", False):  # TODO: Flag to override this
            raise Deleted("Document {db}/{docid} is marked as deleted")
        if "ETag" in resp.headers:
            etag = resp.headers["ETag"]
        else:
            # Conflicts mode
            etag = f'"{blob["_rev"]}"'
        doc = self._blob2doc(blob, db, docid, etag)
        return doc

    # TODO: Attachments

    async def attempt_put_doc(
        self,
        doc,
        db: str | None = None,
        docid: str | None = None,
        *,
        batch: bool = False,
    ):
        """
        Update a document.

        db and docid only need to be given if it's a new document.

        https://docs.couchdb.org/en/stable/api/document/common.html#put--db-docid
        """
        blob, _db, _docid, etag = self._doc2blob(doc)
        await self._request(
            "PUT",
            _db or db,
            _docid or docid,
            params={"batch": "ok"} if batch else {},
            headers={"If-Match": etag} if etag else {},
            json=blob,
        )

    async def attempt_delete_doc(self, doc, *, batch: bool = False):
        """
        Delete a document

        https://docs.couchdb.org/en/stable/api/document/common.html#delete--db-docid
        """
        _, db, docid, etag = self._doc2blob(doc)
        assert db
        assert docid
        await self._request(
            "DELETE",
            db,
            docid,
            params={"batch": "ok"} if batch else {},
            headers={"If-Match": etag},
        )

    async def attempt_copy_doc(self, src_doc, dst_doc, *, batch: bool = False):
        """
        Copy a document

        https://docs.couchdb.org/en/stable/api/document/common.html#copy--db-docid
        """
        # FIXME: Figure out signature

    async def mutate_doc(self, db: str, docid: str) -> AsyncIterator:
        """
        A document mutation loop::

            async for doc in couch.mutate_doc("spam", "eggs"):
                doc.foo = "bar"

        Will replay the mutation until it goes through.
        """
        doc = await self.get_doc(db, docid)
        while True:
            yield doc
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
        for _ in ():
            yield

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
