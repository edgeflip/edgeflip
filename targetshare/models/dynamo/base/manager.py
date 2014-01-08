"""ItemManager

Through ItemManager, an Item class may query its Table for instances.

Item classes may extend ItemManager with class-specific methods, override the default
manager and/or specify alternative managers. (See `Item`.)

"""
from targetshare import utils

from .table import Table
from .request import QueryRequest, Request


inherits_docs = utils.doc_inheritor(Table)


class BaseItemManager(object):

    def __init__(self, table=None):
        self.table = table

    # Proxy Table query methods, but through Request #

    def make_request(self):
        return Request(self.table)

    def filter(self, **kws):
        return self.make_request().filter(**kws)

    def filter_get(self, **kws):
        return self.make_request().filter_get(**kws)

    def prefetch(self, *args, **kws):
        return self.make_request().prefetch(*args, **kws)

    def all(self):
        return self.make_request().all()

    @inherits_docs
    def query_count(self, *args, **kws):
        return self.make_request().query_count(*args, **kws)

    @inherits_docs
    def query(self, *args, **kws):
        return self.make_request().query(*args, **kws)

    @inherits_docs
    def scan(self, *args, **kws):
        return self.make_request().scan(*args, **kws)


class ItemManager(BaseItemManager):
    """Default Item manager.

    Provides interface to Table for Item-specific queries, and base for extensions
    specific to subclasses of Item.

    """
    def batch_get_through(self, *args, **kws):
        return self.make_request().batch_get_through(*args, **kws)

    # Simple proxies -- provide subset of Table interface #

    @inherits_docs
    def batch_get(self, *args, **kws):
        return self.table.batch_get(*args, **kws)

    @inherits_docs
    def get_item(self, *args, **kws):
        return self.table.get_item(*args, **kws)

    @inherits_docs
    def lookup(self, *args, **kws):
        return self.table.lookup(*args, **kws)

    @inherits_docs
    def put_item(self, *args, **kws):
        return self.table.put_item(*args, **kws)

    @inherits_docs
    def delete_item(self, *args, **kws):
        return self.table.delete_item(*args, **kws)

    @inherits_docs
    def batch_write(self, *args, **kws):
        return self.table.batch_write(*args, **kws)

    @inherits_docs
    def count(self):
        return self.table.count()


class AbstractLinkedItemQuery(QueryRequest):

    name_child = child_field = None # required

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


class AbstractLinkedItemManager(BaseItemManager):

    core_keys = query_cls = None # required

    def __init__(self, table, instance):
        super(AbstractLinkedItemManager, self).__init__(table)
        self.instance = instance

    def make_request(self):
        request = super(AbstractLinkedItemManager, self).make_request()
        core_filters = tuple("{}__eq".format(key) for key in self.core_keys)
        instance_filter = dict(zip(core_filters, self.instance.pk))
        return self.query_cls(self.table, self.instance,
                              request.get_query(), **instance_filter)
