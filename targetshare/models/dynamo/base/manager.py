"""ItemManager

Through ItemManager, an Item class may query its Table for instances.

Item classes may extend ItemManager with class-specific methods, override the default
manager and/or specify alternative managers. (See `Item`.)

"""


class ItemManager(object):
    """Default Item manager.

    Provides interface to Table for Item-specific queries, and base for extensions
    specific to subclasses of Item.

    """
    def __init__(self, table=None):
        self.table = table

    # Simple proxies -- provide subset of Table interface #

    def get_item(self, *args, **kws):
        return self.table.get_item(*args, **kws)

    def put_item(self, *args, **kws):
        return self.table.put_item(*args, **kws)

    def delete_item(self, *args, **kws):
        return self.table.delete_item(*args, **kws)

    def batch_get(self, *args, **kws):
        return self.table.batch_get(*args, **kws)

    def batch_write(self, *args, **kws):
        return self.table.batch_write(*args, **kws)

    def count(self):
        return self.table.count()

    def query_count(self, *args, **kws):
        return self.table.query_count(*args, **kws)

    def query(self, *args, **kws):
        return self.table.query(*args, **kws)

    def scan(self, *args, **kws):
        return self.table.scan(*args, **kws)


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
