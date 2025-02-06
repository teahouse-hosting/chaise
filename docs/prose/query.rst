Mango Queries
=============

CouchDB has a feature unofficially called Mango Queries (see :http:post:`/{db}/_find`) which allows for more traditional queries, based on MongoDB's query lanaguage. Chaise extends this to better integrate with its :ref:`document type handling <types>`.

The basic form might be::

    db: chaise.Database = ...

    async for doc in db.find({"username": "beth"}):
        print(doc)

But you probably want to search for documents of a specific type--a concept introduced by Chaise. You can do this with::

    class User:
        ...

    db: chaise.Database = ...

    async for doc in db.find({type: User, "username": "beth"}):
        print(doc)

Note that ``type`` is not quoted; it is literally :class:`type`.

You can also use :ref:`union type expressions <types-union>` (or :data:`typing.Union`) to specify multiple types are acceptable::

    class User:
        ...

    class Bot:
        ...

    db: chaise.Database = ...

    async for doc in db.find({type: User | Bot, "username": "beth"}):
        print(doc)

This feature will interact with Chaise's :ref:`migrations <migrations>` feature: if you define ``Box``, ``Box2``, & ``Box3``, and query for ``Box3``, Chaise will include the migratable types in its searching. (Note that if you ask for ``Box2`` in this case, you'll get ``Box3`` instances.)

This works as expected with complex queries::

    class User:
        ...

    class Bot:
        ...

    db: chaise.Database = ...

    async for doc in db.find({
        "$or": [
            {type: User, "username": "beth"},
            {type: Bot, "owner": "beth"},
        ],
    }):
        print(doc)
