class QueryType:
    def __bool__(self):
        raise TypeError("Can't bool a query fragment")

    def __getattr__(self, name):
        return QAttr(name)

    def __getitem__(self, name):
        return QAttr(name)

    def isinstance(self, cls):
        return Selector({type: cls})


Query = QueryType()


class QAttr:
    name: str

    def __bool__(self):
        raise TypeError("Can't bool a query fragment")

    def __call__(self, inner):
        """
        A way to work with inner objects
        """
        return Selector({self.name: inner})

    def __getattr__(self, name):
        return QAttr(f"{self.name}.{name}")

    def __getitem__(self, name):
        return QAttr(f"{self.name}.{name}")

    def lt(self, other):
        return Selector({self.name: {"$lt": other}})

    def __lt__(self, other):
        return Selector({self.name: {"$lt": other}})

    def le(self, other):
        return Selector({self.name: {"$lte": other}})

    def __le__(self, other):
        return Selector({self.name: {"$lte": other}})

    def eq(self, other):
        return Selector({self.name: {"$eq": other}})

    def __eq__(self, other):
        return Selector({self.name: {"$eq": other}})

    def ne(self, other):
        return Selector({self.name: {"$ne": other}})

    def __ne__(self, other):
        return Selector({self.name: {"$ne": other}})

    def ge(self, other):
        return Selector({self.name: {"$gte": other}})

    def __ge__(self, other):
        return Selector({self.name: {"$gte": other}})

    def gt(self, other):
        return Selector({self.name: {"$gt": other}})

    def __gt__(self, other):
        return Selector({self.name: {"$gt": other}})

    def exists(self, yes: bool = True):
        return Selector({self.name: {"$exists": yes}})

    def isinstance(self, kind: type):
        cnames: dict[type | None, str] = {
            None: "null",
            type(None): "null",
            bool: "boolean",
            int: "number",
            float: "number",
            str: "string",
            list: "array",
            tuple: "array",
            dict: "object",
            object: "object",
        }
        cname: str = cnames[kind]
        return Selector({self.name: {"$type": cname}})

    def in_(self, seq):
        return Selector({self.name: {"$in": seq}})

    def nin(self, seq):
        return Selector({self.name: {"$nin": seq}})

    def issize(self, num):
        return Selector({self.name: {"$size": num}})

    def mod(self, other):
        return Selector({self.name: {"$mod": other}})

    def __mod__(self, other):
        return Selector({self.name: {"$mod": other}})

    def match(self, other):
        return Selector({self.name: {"$regex": other}})

    def beginswith(self, other):
        return Selector({self.name: {"$beginsWith": other}})


# TODO: Attr object for use with $elemMatch, $allMatch, and $keyMapMatch
# Or maybe toss it onto Q? Q.foo.all(Q == "A" | Q == "B")


class Selector(dict):
    def __bool__(self):
        raise TypeError("Can't bool a query fragment")

    # TODO: Apply some basic optimization like combining $and/$or or turn $not+$or into $nor

    def __and__(self, other):
        return Selector({"$and": [self, other]})

    def __rand__(self, other):
        return Selector({"$and": [other, self]})

    def __or__(self, other):
        return Selector({"$or": [self, other]})

    def __ror__(self, other):
        return Selector({"$or": [other, self]})

    def __invert__(self):
        return Selector({"$not": self})

    def nor(self, other):
        return Selector({"$nor": [self, other]})
