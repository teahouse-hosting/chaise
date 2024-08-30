"""
A basic version of chaise that just uses enriched dictionaries as the documents.

:class:`BasicLoader`, :class:`BasicSession`, and :class:`BasicPool` do not do
any migration handling.

:class:`DictRegistry` should be paired with :class:`~chaise.CouchSession` and
:class:`~chaise.SessionPool` if you want some basic document type handling.
"""

from . import DocumentRegistry, CouchSession, SessionPool


class Document(dict):
    """
    A dictionary with some CouchDB attributes
    """

    #: Document ID
    id: str | None = None

    #: Document revision
    rev: str | None = None

    #: Has the document been deleted? (ie, is this a tombstone?)
    deleted: bool = False

    #: Attachment information, if requested
    attachments: dict | None = None

    #: List of conflicts, if requested
    conflicts: list | None = None

    # List of deleted conflicts, if requested
    deleted_conflicts: list | None = None

    #:
    local_seq: str | None = None

    #:
    revs_info: list | None = None

    #:
    revisions: dict | None = None

    def __repr__(self):
        return f"<{type(self).__name__} {self.id!r}@{self.rev!r} {' '.join(f'{k}={v!r}' for k,v in self.items())}>"


class BasicLoader:
    """
    Provides loading without worrying about types or migrations.
    """

    def loadj(self, blob: dict, _kind=Document) -> Document:
        doc = _kind()
        doc.id = blob.pop("_id", None)
        doc.rev = blob.pop("_rev", None)
        doc.deleted = blob.pop("_deleted", False)
        doc.attachments = blob.pop("_attachments", None)
        doc.conflicts = blob.pop("_conflicts", None)
        doc.deleted_conflicts = blob.pop("_deleted_conflicts", None)
        doc.local_seq = blob.pop("_local_seq", None)
        doc.revs_info = blob.pop("_revs_info", None)
        doc.revisions = blob.pop("_revisions", None)
        doc.update(blob)
        return doc

    def dumpj(self, doc: Document) -> dict:
        return (
            doc
            | ({"_id": doc.id} if doc.id is not None else {})
            | ({"_rev": doc.rev} if doc.rev is not None else {})
            | {
                "_deleted": doc.deleted,
                # The rest of it is informational not editable directly
            }
        )


class BasicSession(CouchSession):
    loader = BasicLoader


class BasicPool(SessionPool):
    session_class = BasicSession


class DictRegistry(DocumentRegistry):
    _loader = BasicLoader()

    def load_doc(self, cls: type[Document], blob: dict) -> Document:
        """
        Load a document
        """
        return self._loader.loadj(blob, _kind=cls)

    def dump_doc(self, doc: Document) -> dict:
        """
        Save a document
        """
        return self._loader.dumpj(doc)
