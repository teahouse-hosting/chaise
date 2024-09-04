.. _migrations:

Document Migrations
===================

Ok, so, you're going along, you're extending your app, you're writing
documents, making use of :ref:`types`. But eventually it happens: you need to
make a breaking change.

Chaise can help in the form of migrations.

Migrations refer to the capability to upgrade individual documents automatically
at load time, converting from one registered document class to another.

This might look like::

    @registry.document("Spam")
    class OldSpam:
        has_spam: bool
        has_eggs: bool


    @registry.document("Spam2")
    class Spam:
        has_eggs: bool
        spam_count: int


    @registry.migrate(OldSpam, Spam)
    def migrate_spam(old):
        return Spam(has_eggs=old.has_eggs, spam_count=int(old.has_spam))

In this example, when the Chaise sees that a requested document is of type
``OldSpam``, ``migrate_spam()`` is called to upgrade it, and the resulting
``Spam`` is returned to the user.

.. note::

   The Python class name (``OldSpam`` and ``Spam``) as well as module layout can
   be changed freely. The registered name (``Spam`` and ``Spam2``) must not
   change, or things will break.

.. note::

   The migrated object is not automatically saved back to the database. This is
   handled implicitly when the user mutates a document.
