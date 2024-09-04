.. _types:

Document Type Handling
======================

While CouchDB just works in plain JSON, Python is typeful and classful, and
would generally prefer to keep track of the kinds that objects are. In addition,
a number of struct libraries have sprung up in the ecosystem, like
:mod:`dataclasses`, :mod:`attrs`, and :mod:`pydantic`. Chaise tries to not
prescribe which one of these (or others) you use, but it may have opinions about
how you use them (eg, frozen instances are unsupported).

To this end, :class:`~chaise.DocumentRegistry` handles type tagging through the
:meth:`~chaise.DocumentRegistry.document` decorator. (The passed name is the
type tag stored.)

This means that you can have distinct document classes with methods and schema,
without needing to write individual serializers (see :ref:`integrations` for
details on that).
