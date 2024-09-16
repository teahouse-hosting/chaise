import json
from typing import AsyncIterator, Literal, Callable, Protocol, TypeVar, Generic

import httpx

from . import structs


DOCT = TypeVar("DOCT")


class DocumentLoader(Protocol, Generic[DOCT]):
    """
    Protocol for things that go between JSON blobs and hydrated document
    instances.
    """

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

    Do not use directly. You probably want one of the :ref:`integrations`.
    """

    TYPE_KEY = ""

    _docclasses = {}
    _migrations = []

    def __init_sublcass__(cls):
        cls._docclasses = {}
        cls._migrations = []

    @classmethod
    def _get_class_from_name(cls, name: str) -> type:
        return cls._docclasses[name]

    @classmethod
    def _get_name_from_class(cls, klass: type) -> str:
        for name, kind in cls._docclasses.items():
            if issubclass(klass, kind):  # In case of decorator shenanigans
                return name
        else:
            raise ValueError(f"Couldn't find name for {klass}")

    @classmethod
    def document(cls, name: str):
        """
        Register a class as a loadable couch document.

        Args:
            name: The type identifier to save to CouchDB

        .. note::

           The given name must be globally unique and must never change.
        """
        assert not isinstance(name, type)
        assert name not in cls._docclasses

        def _(klass: type):
            cls._docclasses[name] = klass
            return klass

        return _

    @classmethod
    def migration(cls, before: type, after: type):
        """
        Define a function that'll convert between documents.
        """
        # Normalize to the document classes previously registered
        bname = cls._get_name_from_class(before)
        aname = cls._get_name_from_class(after)
        # Enforce linearity
        assert not any(b == bname for b, _, _ in cls._migrations)

        def _(func: Callable):
            cls._migrations.append((bname, aname, func))
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

    def _migrate(self, bname, doc):
        while funcs := [f for b, _, f in self._migrations if b == bname]:
            (func,) = funcs
            doc = func(doc)
            bname = self._get_name_from_class(type(doc))
        return doc

    def loadj(self, blob):
        type = blob.pop(self.TYPE_KEY)
        klass = self._get_class_from_name(type)
        doc = self.load_doc(klass, blob)
        doc = self._migrate(type, doc)
        return doc

    def dumpj(self, doc):
        blob = self.dump_doc(doc)
        blob[self.TYPE_KEY] = self._get_name_from_class(type(doc))
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

    You probably want to override like::

        class MySession(CouchSession):
            loader = MyRegistry

    """

    _client: httpx.AsyncClient
    _root: httpx.URL

    #: Class responsible for de/serializing data.
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
            elif isinstance(value, str):
                rv[key] = value
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

    def __getitem__(self, key: str) -> "Database":
        """
        Gets a database.

        (Does not actually check if it exists.)
        """
        return Database(self, key)

    async def get_db(self, dbname: str) -> "Database":
        """
        Gets a database. Checks if it exists.

        See :http:head:`/{db}`
        """
        await self._request("HEAD", dbname)
        return Database(self, dbname)

    async def create_db(
        self,
        dbname: str,
        *,
        shards: int | None = None,
        replicas: int | None = None,
        partitioned: bool | None = None,
    ) -> "Database":
        """
        Create a database

        See :http:post:`/{db}`
        """
        try:
            await self._request(
                "PUT",
                dbname,
                params={
                    "q": shards,
                    "n": replicas,
                    "partitioned": partitioned,
                },
            )
        except httpx.HTTPStatusError as exc:
            match exc.response.status_code:
                case 412:
                    raise Conflict("Database already exists") from exc
                case _:
                    raise
        return Database(self, dbname)

    async def delete_db(self, dbname: str):
        """
        Delete a database.

        See :http:delete:`/{db}`
        """
        await self._request("DELETE", dbname)

    async def iter_dbs(self) -> AsyncIterator[str]:
        """
        List all databases

        See :http:get:`/_all_dbs`
        """
        resp = await self._request("GET", "_all_dbs")
        for dbname in resp.json():
            yield dbname

    # TODO: Database metadata


class Database:
    """
    An individual database.
    """

    def __init__(self, session, name):
        """
        :private:
        """
        self._session = session
        self._name = name

    def _blob2doc(self, blob, db, docid, etag=...):
        if docid is ...:
            docid = blob["_id"]
        if etag is ...:
            etag = f'"{blob["_rev"]}"'
        doc = self._session.loader().loadj(blob)
        doc.__db = db
        doc.__docid = docid
        doc.__etag = etag
        return doc

    def _doc2blob(self, doc):
        blob = self._session.loader().dumpj(doc)
        db = docid = etag = None
        try:
            db = doc.__db
            docid = doc.__docid
            etag = doc.__etag
        except AttributeError:
            pass
        return blob, db, docid, etag

    async def get(
        self,
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

        See :http:get:`/{db}/{docid}`
        """
        resp = await self._session._request(
            "GET",
            self._name,
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
            raise Deleted("Document {self._name}/{docid} is marked as deleted")
        if "ETag" in resp.headers:
            etag = resp.headers["ETag"]
        else:
            # Conflicts mode
            etag = f'"{blob["_rev"]}"'
        doc = self._blob2doc(blob, self._name, docid, etag)
        return doc

    # TODO: Attachments

    async def attempt_put(
        self,
        doc,
        docid: str | None = None,
        *,
        batch: bool = False,
    ):
        """
        Update a document.

        db and docid only need to be given if it's a new document.

        See :http:put:`/{db}/{docid}`
        """
        blob, _db, _docid, etag = self._doc2blob(doc)
        assert _db is None or _db == self._name
        await self._session._request(
            "PUT",
            self._name,
            _docid or docid,
            params={"batch": "ok"} if batch else {},
            headers={"If-Match": etag} if etag else {},
            json=blob,
        )

    async def attempt_delete(self, doc, *, batch: bool = False):
        """
        Delete a document

        See :http:delete:`/{db}/{docid}`
        """
        _, db, docid, etag = self._doc2blob(doc)
        assert db == self._name
        assert docid
        await self._session._request(
            "DELETE",
            db,
            docid,
            params={"batch": "ok"} if batch else {},
            headers={"If-Match": etag},
        )

    async def attempt_copy(self, src_doc, dst_doc, *, batch: bool = False):
        """
        Copy a document

        .. todo::

           Implement

        See :http:copy:`/{db}/{docid}`
        """
        # FIXME: Figure out signature

    async def mutate(self, docid: str) -> AsyncIterator:
        """
        A document mutation loop::

            async for doc in couch.mutate_doc("spam"):
                doc.foo = "bar"

        Will replay the mutation until it goes through.
        """
        doc = await self.get(docid)
        while True:
            yield doc
            try:
                await self.attempt_put(doc)
            except Conflict:
                doc = await self.get(docid)
            else:
                break

    async def iter_all_docs(
        self, include_docs: bool = False
    ) -> AsyncIterator[structs.AllDocs_DocRef]:
        """
        List all documents

        TODO: More params

        Args:
            include_docs: Pre-load documents

        See :http:get:`/{db}/_all_docs`
        """
        resp = await self._session._request(
            "GET",
            self._name,
            "_all_docs",
            params={
                "include_docs": include_docs,
            },
            headers={
                "Accept": "application/json",
            },
        )
        blob = resp.json()
        for ref in blob["rows"]:
            if "doc" in ref:
                doc = self._blob2doc(ref["doc"], self._name, ref["id"])
            else:
                doc = None
            yield structs.AllDocs_DocRef(
                _db=self, docid=ref["id"], rev=ref["value"]["rev"], _doc=doc
            )

    # TODO: Mango searches
    # TODO: Database operations


class SessionPool:
    """
    Responsible for giving out Couch connections.

    You probably want to override like::

        class MyPool(SessionPool):
            session_class = MySession
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
