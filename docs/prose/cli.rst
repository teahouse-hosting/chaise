Chaise CLI
==========

While CouchDB does not have schema in the traditional sense, it does have :external+couchdb:ref:`views <views>`, :external+couchdb:ref:`indexes <api/db/find/index>`, and :external+couchdb:ref:`design docs <ddocs>`. Chaise allows you to manages these declaratively through a CLI, similar to migrations in SQL land.

The Directory Structure
-----------------------

Chaise uses database and index declarations written in `KDL <https://kdl.dev/>` in a directory structure::

    mycouch
    ├── first-db
    │   └── __db__.kdl
    ├── second-db
    │   └── __db__.kdl
    └── interesting-db
        ├── a-ddoc.kdl
        └── __db__.kdl

Each directory with a ``__db__.kdl`` represents one CouchDB database (collection in other NoSQLs). Next to that ``__db__.kdl`` are files describing individual design docs.

Database descriptions
~~~~~~~~~~~~~~~~~~~~~

Databases managed by Chaise are indicated by a ``__db__.kdl``. The name by default is the directory name, and other database options may be set here.

The ``__db__.kdl`` file may be empty:

.. code-block:: kdl
   :caption: __db__.kdl

Or it can have a empty ``database`` node:

.. code-block:: kdl
   :caption: __db__.kdl

   database

Or it the database name can be changed:

.. code-block:: kdl
   :caption: __db__.kdl

   database "foo/bar"

Design Documents
~~~~~~~~~~~~~~~~

A design document is represented by a single KDL file next to a ``__db__.kdl`` file. It either consists of one or more indexes (for use with mango queries) or one or more views (not yet implemented). You cannot mix indexes and views in the same

Each index consists of a name and one or more fields. They can be listed individually:

.. code-block:: kdl
    :caption: long-kdl.kdl

    index "foo" {
        field "spam"
        field "eggs"
    }


Or together:

.. code-block:: kdl
    :caption: short-kdl.kdl

    index "bar" {
        fields "quux" "baz"
    }

(These styles can be mixed and matched.)



The ``apply`` command
---------------------

To actually add databases and design docs to CouchDB, call the CLI command ``chaise apply``. It requires two arguments:

* The server, specified either with ``--server`` or the environment variable ``$COUCHDB_URL``
* The location to find database directories, specified as a Python module.

When called, it'll reach out to the server, add missing databases, and update design documents.
