Attrs
=====

The attrs integration utilizes :mod:`attrs` and :mod:`cattrs` to handle schema
and typing.

::

    class MyRegistry(chaise.attrs.AttrsRegistry):
        pass


    class MySession(chaise.CouchSession):
        loader = MyRegistry


    class MyPool(chaise.helpers.ConstantPoolMixin, chaise.SessionPool):
        session_class = DictSession


    @MyRegistry.document("Snake")
    class Snake:
        pass


    pool = MyPool(os.environ['COUCHDB_URL'])
    session = await pool.session()
    db = await session.get_db('snakes')
    doc = await db.get('okeetee')


:meth:`~chaise.attrs.AttrsRegistry.document` handles calling :func:`attrs.define`
for you and will pass through keyword arguments, with the addition of
``slots=False``.

:data:`chaise.attrs.converter` is configured with either :mod:`cattrs.preconf.ujson`
or :mod:`cattrs.preconf.json`, depending on what's available to import. This
means that most of core and standard library types are supported.
