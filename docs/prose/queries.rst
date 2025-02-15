Example Mango Queries
=====================

* JSON: The native Mango queries
* KDL: A hypothetical KDL version (probably won't implement, since it's too little value)
* Python: The Python query builder

.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "year": {"$gt": 2010}
        }

.. tab:: KDL

    .. code-block:: KDL

        year $gt 2010

.. tab:: Python

    .. code-block:: Python

        Q.year > 2010


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "director": "Lars von Trier"
        }

.. tab:: KDL

    .. code-block:: KDL

        director $eq "Lars von Trier"

.. tab:: Python

    .. code-block:: Python

        Q.director == "Lars von Trier"


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "title": "Live And Let Die"
        }

.. tab:: KDL

    .. code-block:: KDL

        title $eq "Live And Let Die"

.. tab:: Python

    .. code-block:: Python

        Q.title == "Live And Let Die"


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "name": "Paul",
            "location": "Boston"
        }

.. tab:: KDL

    .. code-block:: KDL

        name $eq "Paul"
        location $eq "Boston"

.. tab:: Python

    .. code-block:: Python

        Q.name == "Paul" & Q.location == "Boston"


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "imdb": {
                "rating": 8
            }
        }

.. tab:: KDL

    .. code-block:: KDL

        imdb {
            rating $eq 8
        }

.. tab:: Python

    .. code-block:: Python

        Q.imdb(Q.rating == 8)


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "imdb.rating": 8
        }

.. tab:: KDL

    .. code-block:: KDL

        imdb.rating $eq 8

.. tab:: Python

    .. code-block:: Python

        Q.imdb.rating == 8


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "$and": [
                {
                    "director": {
                        "$eq": "Lars von Trier"
                    }
                },
                {
                    "year": {
                        "$eq": 2003
                    }
                }
            ]
        }

.. tab:: KDL

    .. code-block:: KDL

        $and {
            director $eq "Lars von Trier"
            year $eq 2003
        }

.. tab:: Python

    .. code-block:: Python

        Q.director == "Lars von Trier" & Q.year == 2003


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "$and": [
                {
                    "title": "Total Recall"
                },
                {
                    "year": {
                        "$in": [1984, 1991]
                    }
                }
            ]
        }

.. tab:: KDL

    .. code-block:: KDL

        $and {
            title $eq "Total Recall"
            year $in 1984 1991
        }

.. tab:: Python

    .. code-block:: Python

        Q.title == "Total Recall" & Q.year.in_(1984, 1991)


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "$and": [
                {
                    "_id": { "$gt": null }
                },
                {
                    "year": {
                        "$in": [2014, 2015]
                    }
                }
            ]
        }

.. tab:: KDL

    .. code-block:: KDL

        $and {
            _id $gt #null
            year $in 2014 2015
        }

.. tab:: Python

    .. code-block:: Python

        Q._id > None & Q.year.in_(2014, 2015)


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "year": 1977,
            "$or": [
                { "director": "George Lucas" },
                { "director": "Steven Spielberg" }
            ]
        }

.. tab:: KDL

    .. code-block:: KDL

        year $eq 1977
        $or {
            director $eq "George Lucas"
            director $eq "Steven Spielberg"
        }

.. tab:: Python

    .. code-block:: Python

        Q.year == 1977 & (Q.director == "George Lucas" | Q.director == "Steven Spielberg")


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "year": {
                "$gte": 1900,
                "$lte": 1903
            },
            "$not": {
                "year": 1901
            }
        }

.. tab:: KDL

    .. code-block:: KDL

        year {
            $gte 1900
            $lte 1903
        }
        $not {
            year $eq 1901
        }

.. tab:: KDL

    .. code-block:: KDL

        year {
            $gte 1900
            $lte 1903
        }
        $not year $eq 1901

.. tab:: Python

    .. code-block:: Python

        Q.year >= 1900 & Q.year <= 1903 & ~(Q.year == 1901)


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "year": {
                "$gte": 1900,
                "$lte": 1910
            },
            "$nor": [
                { "year": 1901 },
                { "year": 1905 },
                { "year": 1907 }
            ]
        }

.. tab:: KDL

    .. code-block:: KDL

        year {
            $gte 1900
            $lte 1910
        }
        $nor {
            year $eq 1901
            year $eq 1905
            year $eq 1907
        }

.. tab:: Python

    .. code-block:: Python

        Q.year >= 1900 & Q.year <= 1903 & ~(Q.year == 1901 | Q.year == 1905 | Q.year == 1907)


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "_id": {
                "$gt": null
            },
            "genre": {
                "$all": ["Comedy","Short"]
            }
        }

.. tab:: KDL

    .. code-block:: KDL

        _id $gt #null
        genre $all Comedy Short

.. tab:: Python

    .. code-block:: Python

        Q._id > None & NotImplemented


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "_id": { "$gt": null },
            "genre": {
                "$elemMatch": {
                    "$eq": "Horror"
                }
            }
        }

.. tab:: KDL

    .. code-block:: KDL

        _id $gt #null
        genre $elemMatch {
            $eq Horror
        }

.. tab:: Python

    .. code-block:: Python

        Q._id > None & NotImplemented


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "_id": { "$gt": null },
            "genre": {
                "$allMatch": {
                    "$eq": "Horror"
                }
            }
        }

.. tab:: KDL

    .. code-block:: KDL

        _id $gt #null
        genre $allMatch {
            $eq Horror
        }

.. tab:: Python

    .. code-block:: Python

        Q._id > None & NotImplemented


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "_id": { "$gt": null },
            "cameras": {
                "$keyMapMatch": {
                    "$eq": "secondary"
                }
            }
        }

.. tab:: KDL

    .. code-block:: KDL

        _id $gt #null
        cameras $keyMapMatch {
            $eq secondary
        }

.. tab:: Python

    .. code-block:: Python

        Q._id > None & NotImplemented


.. tab:: JSON
    :new-set:

    .. code-block:: JSON

        {
            "afieldname": {"$regex": "^A"}
        }

.. tab:: KDL

    .. code-block:: KDL

        afieldname $regex "^A"

.. tab:: Python

    .. code-block:: Python

        Q.afieldname.match(r"^A")
