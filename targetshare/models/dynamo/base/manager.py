"""ItemManager

Through ItemManager, an Item class may query its Table for instances.

Item classes may extend ItemManager with class-specific methods, override the default
manager and/or specify alternative managers. (See `Item`.)

"""
import collections

from boto.dynamodb2 import fields as basefields

from targetshare import utils

from .table import Table
from .utils import cached_property


inherits_docs = utils.doc_inheritor(Table)


class Query(dict):

    def __init__(self, table, *args, **kws):
        super(Query, self).__init__(*args, **kws)
        self.table = table
        self.links = None

    def clone(self, **kws):
        klone = type(self)(self.table, self, **kws)
        klone.links = self.links
        return klone

    def filter(self, **kws):
        return self.clone(**kws)

    def copy(self):
        return self.clone()

    def prefetch(self, *linked):
        clone = self.copy()
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

    @inherits_docs
    def query(self, *args, **kws):
        filters = self.filter(**kws)
        results = self.table.query(*args, **filters)
        return self._process_results(results)

    @inherits_docs
    def scan(self, *args, **kws):
        filters = self.filter(**kws)
        results = self.table.scan(*args, **filters)
        return self._process_results(results)

    @inherits_docs
    def query_count(self, *args, **kws):
        filters = self.filter(**kws)
        return self.table.query_count(*args, **filters)

    def __repr__(self):
        return "<{}({}: {}>".format(self.__class__.__name__,
                                    self.table.short_name,
                                    super(Query, self).__repr__())


class BaseItemManager(object):

    def __init__(self, table=None):
        self.table = table

    # Proxy Table query methods, but through Query #

    def get_query(self):
        return Query(self.table)

    def filter(self, **kws):
        return self.get_query().filter(**kws)

    def prefetch(self, *args, **kws):
        return self.get_query().prefetch(*args, **kws)

    @inherits_docs
    def query_count(self, *args, **kws):
        return self.get_query().query_count(*args, **kws)

    @inherits_docs
    def query(self, *args, **kws):
        return self.get_query().query(*args, **kws)

    @inherits_docs
    def scan(self, *args, **kws):
        return self.get_query().scan(*args, **kws)


class ItemManager(BaseItemManager):
    """Default Item manager.

    Provides interface to Table for Item-specific queries, and base for extensions
    specific to subclasses of Item.

    """
    # Simple proxies -- provide subset of Table interface #

    @inherits_docs
    def get_item(self, *args, **kws):
        return self.table.get_item(*args, **kws)

    @inherits_docs
    def put_item(self, *args, **kws):
        return self.table.put_item(*args, **kws)

    @inherits_docs
    def delete_item(self, *args, **kws):
        return self.table.delete_item(*args, **kws)

    @inherits_docs
    def batch_get(self, *args, **kws):
        return self.table.batch_get(*args, **kws)

    @inherits_docs
    def batch_write(self, *args, **kws):
        return self.table.batch_write(*args, **kws)

    @inherits_docs
    def count(self):
        return self.table.count()


class AbstractLinkedItemQuery(Query):

    db_key = name_child = child_field = None # required

    def __init__(self, table, instance, *args, **kws):
        super(AbstractLinkedItemQuery, self).__init__(table, *args, **kws)
        self.instance = instance

    def clone(self, **kws):
        klone = type(self)(self.table, self.instance, self, **kws)
        klone.links = self.links
        return klone

    def _process_results(self, results):
        results = super(AbstractLinkedItemQuery, self)._process_results(results)
        if self.links is None or (self.links and self.name_child not in self.links):
            # No prefetch specified or limited prefetch specified;
            # post-process results to include parent reference:
            results.iterable = self._populate_parent_cache(results.iterable)
        return results

    def _populate_parent_cache(self, iterable):
        for item in iterable:
            cached = self.child_field.cache_get(self.name_child, item)
            if cached is None:
                self.child_field.cache_set(self.name_child, item, self.instance)
            yield item

    @cached_property
    def _hash_keys(self):
        return {field.name for field in self.table.schema
                if isinstance(field, basefields.HashKey)}

    def all(self):
        if any(key in self._hash_keys for key in self.db_key):
            return self.query()
        return self.scan()

    def get(self, **kws):
        results = iter(self.filter(**kws).all())
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


class AbstractLinkedItemManager(BaseItemManager):

    core_filters = query_cls = None # required

    def __init__(self, table, instance):
        super(AbstractLinkedItemManager, self).__init__(table)
        self.instance = instance

    def get_query(self):
        query = super(AbstractLinkedItemManager, self).get_query()
        instance_filter = dict(zip(self.core_filters, self.instance.pk))
        return self.query_cls(self.table, self.instance, query, **instance_filter)

    def all(self):
        return self.get_query().all()

    def get(self, **kws):
        return self.get_query().get(**kws)
