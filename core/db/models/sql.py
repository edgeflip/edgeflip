import functools
import hashlib
import numbers


DEFAULT_ENCODING = 'utf-8'

SORTABLES = (set, frozenset)
ITERABLES = (tuple, list)
CONTAINERS = SORTABLES + ITERABLES


# Utilities to serialize the opaque sql.Query to standard Python #

def structreplace(value, **replacements):
    """Reconstruct the given object with specified types replaced.

        >>> structreplace([100, 'hi'], int=long, str=lambda s: s.decode('utf-8'))
        [100L, u'hi']

    """
    cls = type(value)
    replacement = replacements.get(cls.__name__, cls)

    if isinstance(value, CONTAINERS):
        value = (structreplace(element, **replacements) for element in value)

    return replacement(value)


def _serialize_tables(query):
    aliased = frozenset(alias for (alias, count) in query.alias_refcount.iteritems() if count)
    return aliased or frozenset([query.model._meta.db_table])


def _serialize_conditions(conditions):
    return frozenset(
        (constraint.alias, constraint.col, operator, annotation, param)
        for (constraint, operator, annotation, param) in conditions
    )


def _serialize_where(where):
    return (
        where.negated, # NOT ... ?
        where.connector, # AND/OR ?
        _serialize_conditions(where.children),
    ) if where.children else ()


def serialize_query(query, standardize=True, encoding=DEFAULT_ENCODING):
    """Serialize a sql.Query to standard Python.

    According to parameter `standardize`, and by default, ints are converted to
    longs and strs are decoded. strs are decoded as utf-8, unless `encoding` is
    specified.

    """
    # serialize: FROM, WHERE
    # not supporting: SELECT, GROUP BY, HAVING
    # TODO: LIMIT+ORDER_BY?
    serialization = (_serialize_tables(query), _serialize_where(query.where))
    if standardize:
        decode = functools.partial(unicode, encoding=encoding)
        return structreplace(serialization, int=long, str=decode)
    return serialization


# ... and create an md5 hash of this serialization #

def walkstruct(value):
    """Generate a stream of the given object and any objects it contains
    (recursively).

    For consistency, sets and frozensets are iterated in sorted order.

    """
    yield value

    if isinstance(value, SORTABLES):
        value = sorted(value)

    if isinstance(value, ITERABLES):
        for element in value:
            for result in walkstruct(element):
                yield result


class md5ObjectHash(object):
    """md5 hash constructor, modeled after hashlib.md5, but which, in addition
    to str, accepts: set, frozenset, list, tuple, built-in string and numeric
    types.

    unicode is encoded as utf-8, unless `encoding` is specified.

    """
    notset = object()

    def __init__(self, initial=notset, encoding=DEFAULT_ENCODING):
        self.md5 = hashlib.md5()
        self.encoding = encoding
        if initial is not self.notset:
            self.update(initial)

    def _update(self, element):
        self.md5.update(str(type(element)))
        if isinstance(element, basestring):
            self.md5.update(element.encode(self.encoding))
        elif isinstance(element, numbers.Number):
            self.md5.update(str(element))
        elif not isinstance(element, CONTAINERS):
            raise TypeError("unhashable type, {}".format(type(element)))

    def update(self, value):
        for element in walkstruct(value):
            self._update(element)

    def hexdigest(self):
        return self.md5.hexdigest()


def hash_query(query, encoding=DEFAULT_ENCODING):
    """Generate an md5 hash digest identifying the given sql.Query.

    utf-8 is the assumed database character encoding, unless `encoding` is
    specified.

    """
    serialization = serialize_query(query, encoding=encoding)
    return md5ObjectHash(serialization, encoding=encoding).hexdigest()
