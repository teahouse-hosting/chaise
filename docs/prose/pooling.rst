.. _pooling:

Connection Pooling
==================

Chaise fully supports CouchDB clusters of all kinds--any kind that has multiple
accessible URLs. In addition, it utilizes the connection pooling of its
underlying library HTTPX_.

.. _httpx: https://www.python-httpx.org/

This is handled through the :class:`~chaise.SessionPool` class. Pooling is automatic,
while clustering is implemented with  the :func:`~chaise.SessionPool.iter_servers`
method. It is intended that this method be overriden by the user, although
:class:`~chaise.helpers.ConstantPoolMixin` and :class:`~chaise.helpers.DnsPoolMixin`
are provided for simple use cases.

No matter what, :http:get:`/_up` is called before giving the user a session, so
the user is guaranteed to get a live server (at least at the time it's returned).
