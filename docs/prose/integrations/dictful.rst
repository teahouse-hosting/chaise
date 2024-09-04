Dictful
=======

The "dictful" system is a small addition to the :ref:`integration-basic` to add
type and migration handling. There still isn't any schema handling.

::

    class MyRegistry(chaise.dictful.DictRegistry):
        pass


    class MySession(chaise.CouchSession):
        loader = MyRegistry


    class MyPool(chaise.helpers.ConstantPoolMixin, chaise.SessionPool):
        session_class = DictSession


    @MyRegistry.document("Snake")
    class Snake(chaise.dictful.Document):
        pass


    pool = MyPool(os.environ['COUCHDB_URL'])
    session = await pool.session()
    db = await session.get_db('snakes')
    doc = await db.get('okeetee')
