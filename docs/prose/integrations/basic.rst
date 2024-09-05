.. _integration-basic:

Basic
=====

The "basic" "integration" is just a thin wrapper around dictionaries. It
completely eschews the typing and migration systems and performs no schema
checking, or even declarations.

If you're writing an agnostic tool, or want a quick start, this is probably the
integration you want.

To use this integration, override :class:`~chaise.dictful.BasicPool` per
:ref:`pooling`. You do not need to define a registry or a session.

An example of usage::

    class MyPool(chaise.helpers.ConstantPoolMixin, chaise.dictful.BasicPool):
        pass


    pool = MyPool(os.environ['COUCHDB_URL'])
    session = await pool.session()
    db = await session.get_db('snakes')
    doc = await db.get('okeetee')

At the end of this, ``doc`` will be a :class:`~chaise.dictful.Document`, which
is a :class:`dict` with some extra attributes.
