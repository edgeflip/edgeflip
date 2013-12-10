"""ItemManager

Through ItemManager, an Item class may query its Table for instances.

Item classes may extend ItemManager with class-specific methods, override the default
manager and/or specify alternative managers. (See `Item`.)

"""
from targetshare import utils

from .table import Table


inherits_docs = utils.doc_inheritor(Table)


class Query(dict):

    def __init__(self, table, *args, **kws):
        super(Query, self).__init__(*args, **kws)
        self.table = table

    def copy(self):
        return type(self)(self.table, self)

    def filter(self, **kws):
        return type(self)(self.table, self, **kws)

    @inherits_docs
    def query_count(self, *args, **kws):
        filters = self.filter(**kws)
        return self.table.query_count(*args, **filters)

    @inherits_docs
    def query(self, *args, **kws):
        filters = self.filter(**kws)
        return self.table.query(*args, **filters)

    @inherits_docs
    def scan(self, *args, **kws):
        filters = self.filter(**kws)
        return self.table.scan(*args, **filters)

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


class ItemManagerDescriptor(object):
    """Descriptor wrapper for ItemManagers.

    Allows access to the manager via the class and access to any hidden attributes
    via the instance.

    """
    def __init__(self, manager, name):
        self.manager = manager
        self.name = name

    def __get__(self, instance, cls=None):
        # Access to manager from class is fine:
        if instance is None:
            return self.manager

        # Check if there's a legitimate instance method we're hiding:
        try:
            # Until we support inheritance of ItemManagers through
            # Item classes, super(cls, cls) will do:
            hidden = getattr(super(cls, cls), self.name)
        except AttributeError:
            pass
        else:
            # Bind and return hidden method:
            return hidden.__get__(instance, cls)

        # Let them know they're wrong:
        cls_name = getattr(cls, '__name__', '')
        raise AttributeError("Manager isn't accessible via {}instances"
                             .format(cls_name + ' ' if cls_name else cls_name))

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.name)
