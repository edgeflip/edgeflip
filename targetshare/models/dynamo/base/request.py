import collections
import functools
import logging

from boto.dynamodb2 import fields as basefields

from targetshare import utils

from . import loading
from .table import Table
from .types import AbstractSetType
from .utils import cached_property


LOG = logging.getLogger('boto')

inherits_docs = utils.doc_inheritor(Table)


class BaseRequest(object):

    def prefetch(self, *linked):
        clone = self.clone()
        if clone.links is None or not linked:
            clone.links = set()
        clone.links.update(linked)
        return clone

    def _prefetch(self, iterable):
        all_links = self.table.item._meta.links
        if self.links:
            link_fields = [(link, all_links[link]) for link in self.links]
        else:
            link_fields = all_links.items()

        primaries = []
        gets = collections.defaultdict(set)
        for primary in iterable:
            primaries.append(primary)
            for (link, field) in link_fields:
                pk = field.get_item_pk(primary)
                if all(pk):
                    gets[link].add(pk)

        results = collections.defaultdict(dict)
        for (link, field) in link_fields:
            manager = field.item.items
            key_fields = manager.table.get_key_fields()
            keys = [dict(zip(key_fields, values)) for values in gets[link]]
            for linked in manager.batch_get(keys=keys):
                results[link][linked.pk] = linked

        for primary in primaries:
            for (link, field) in link_fields:
                pk = field.get_item_pk(primary)
                if all(pk):
                    try:
                        linked = results[link][pk]
                    except KeyError:
                        pass
                    else:
                        field.cache_set(link, primary, linked)

            yield primary

    def _process_results(self, results):
        if self.links is None:
            return results
        results.iterable = self._prefetch(results.iterable)
        return results

    def __iter__(self):
        return iter(self.all())

    def __repr__(self):
        return "<{}({})>".format(self.__class__.__name__, self.table.short_name)


def processed(func):
    @functools.wraps(func)
    def wrapped(self, *args, **kws):
        results = func(self, *args, **kws)
        return self._process_results(results)
    return wrapped


class Request(BaseRequest):

    def __init__(self, table):
        self.table = table
        self.links = None

    def clone(self, cls=None, *args, **kws):
        cls = cls or type(self)
        klone = cls(self.table, *args, **kws)
        klone.links = self.links
        return klone

    @inherits_docs
    @processed
    def batch_get(self, *args, **kws):
        return self.table.batch_get(*args, **kws)

    # NOTE: Could support batch_get_through through link fields, etc.
    # NOTE: Might help with links that would otherwise scan, though unclear
    # NOTE: whether this is faster than a query.
    # NOTE: E.g. ItemLinkField('User', db_key=fbid, through='PostInteractionsSet')

    def batch_get_through(self, join, *args, **kws):
        if isinstance(join, basestring):
            join = loading.cache[join]

        # Parse out join table's schema:
        link_keys = []
        link_set = None
        for (key, field) in join._meta.keys.items():
            if key != join.update_field:
                if isinstance(field.data_type, AbstractSetType):
                    if link_set is None:
                        link_set = key
                    else:
                        raise TypeError("Ambiguous join table schema: multiple set fields")
                else:
                    link_keys.append(key)
        if link_set is None:
            raise TypeError("Invalid join table schema: no set field")

        # Assume courtesy of non-set field names matching (for now),
        # but allow set field name to be arbitrary:
        try:
            (set_key,) = (key for key in self.table.get_key_fields()
                          if key not in link_keys)
        except ValueError:
            raise TypeError("Mismatched join table schema: could not determine "
                            "set field's corresponse in primary table")
        else:
            all_keys = link_keys + [set_key]

        def gen_flat(): # Ensure laziness
            for link in join.items.batch_get(*args, **kws):
                values = tuple(getattr(link, key) for key in link_keys)
                for set_value in getattr(link, link_set):
                    yield dict(zip(all_keys, values + (set_value,)))

        return self.batch_get(keys=utils.LazyList(gen_flat()))

    def get_query(self, *args, **kws):
        return self.clone(QueryRequest, *args, **kws)

    def filter(self, **kws):
        return self.get_query(**kws)

    def filter_get(self, **kws):
        return self.get_query().filter_get(**kws)

    def all(self):
        return self.get_query().all()

    @inherits_docs
    def query(self, *args, **kws):
        return self.get_query().query(*args, **kws)

    @inherits_docs
    def scan(self, *args, **kws):
        return self.get_query().scan(*args, **kws)

    @inherits_docs
    def query_count(self, *args, **kws):
        return self.get_query().query_count(*args, **kws)


class QueryRequest(BaseRequest, dict):

    def __init__(self, table, *args, **kws):
        super(QueryRequest, self).__init__(*args, **kws)
        self.table = table
        self.links = None

    def clone(self, **kws):
        klone = type(self)(self.table, self, **kws)
        klone.links = self.links
        return klone

    def copy(self):
        return self.clone()

    def filter(self, **kws):
        return self.clone(**kws)

    @inherits_docs
    @processed
    def query(self, *args, **kws):
        filters = self.filter(**kws)
        return self.table.query(*args, **filters)

    @inherits_docs
    @processed
    def scan(self, *args, **kws):
        filters = self.filter(**kws)
        return self.table.scan(*args, **filters)

    @inherits_docs
    def query_count(self, *args, **kws):
        filters = self.filter(**kws)
        return self.table.query_count(*args, **filters)

    @cached_property
    def _hash_keys(self):
        return {field.name for field in self.table.schema
                if isinstance(field, basefields.HashKey)}

    @property
    def _opless(self):
        return (key.rsplit('__', 1)[0] for key in self.iterkeys())

    def all(self):
        if 'index' in self or any(key in self._hash_keys for key in self._opless):
            return self.query()
        LOG.warning('Performed implicit scan %r', self)
        return self.scan()

    def filter_get(self, **kws):
        results = iter(self.filter(**kws))
        try:
            result = next(results)
        except StopIteration:
            # Couldn't find the one:
            raise self.table.item.DoesNotExist

        try:
            next(results)
        except StopIteration:
            # Was only the one, as expected
            return result

        # There were more than one:
        raise self.table.item.MultipleItemsReturned

    def __repr__(self):
        return "<{}({}: {!r})>".format(self.__class__.__name__,
                                       self.table.short_name,
                                       dict(self))
