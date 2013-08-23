import types

from boto.dynamodb2 import fields, results, table, items

from . import db


# Subclass boto's BatchGetResultSet to prevent fetch_more() from bailing
# when any one batch is empty.

# WARNING: Upgrading boto? Upgrade this too! #

# Start BatchGetResultSet patch #

class BatchGetResultSet(results.BatchGetResultSet):

    # Copy of BatchGetResultSet's fetch_more (except for %%):
    def fetch_more(self):
        self._reset()

        args = self.call_args[:]
        kwargs = self.call_kwargs.copy()

        # Slice off the max we can fetch.
        kwargs['keys'] = self._keys_left[:self._max_batch_get]
        self._keys_left = self._keys_left[self._max_batch_get:]

        results = self.the_callable(*args, **kwargs)

        # %% Comment out bail condition:
        #if not len(results.get('results', [])):
        #    self._results_left = False
        #    return
        # %% Instead just ensure response is well-formed:
        results.setdefault('results', [])

        self._results.extend(results['results'])

        for offset, key_data in enumerate(results.get('unprocessed_keys', [])):
            # We've got an unprocessed key. Reinsert it into the list.
            # DynamoDB only returns valid keys, so there should be no risk of
            # missing keys ever making it here.
            self._keys_left.insert(offset, key_data)

        if len(self._keys_left) <= 0:
            self._results_left = False

        # Decrease the limit, if it's present.
        if self.call_kwargs.get('limit'):
            self.call_kwargs['limit'] -= len(results['results'])

        # %% If we didn't actually get any results, try again:
        if self._results_left and not self._results:
            self.fetch_more()

# End BatchGetResultSet patch #


# Subclass boto's Table to convert ResultSets and Items to ours.

class Table(table.Table):

    def __init__(self, table_name, schema=None, throughput=None, indexes=None,
                 connection=None,
                 item=None): # Add "item" to inherited interface
        super(Table, self).__init__(table_name, schema, throughput, indexes, connection)
        self.item = item

    @staticmethod
    def _convert(instance, new_type):
        """Convert a boto object to the given edgeflip type."""
        new = new_type()
        new.__dict__ = instance.__dict__
        return new

    # Use our BatchGetResultSet rather than boto's #

    def batch_get(self, *args, **kws):
        result = super(Table, self).batch_get(*args, **kws)
        return self._convert(result, BatchGetResultSet)

    # Use our Item rather than boto's #

    # TODO: BatchTable uses internal Item. If we want to override e.g.
    # its use of prepare_full....

    def get_item(self, *args, **kws):
        item = super(Table, self).get_item(*args, **kws)
        return self._convert(item, self.item)

    def put_item(self, data, overwrite=False):
        item = self.item(self, data=data)
        return item.save(overwrite=overwrite)

    def _batch_get(self, *args, **kws):
        result = super(Table, self)._batch_get(*args, **kws)
        result['results'] = [self._convert(item, self.item) for item in result['results']]
        return result

    def _query(self, *args, **kws):
        result = super(Table, self)._query(*args, **kws)
        result['results'] = [self._convert(item, self.item) for item in result['results']]
        return result

    def _scan(self, *args, **kws):
        result = super(Table, self)._scan(*args, **kws)
        result['results'] = [self._convert(item, self.item) for item in result['results']]
        return result


class ItemManager(object):

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

    def __init__(self, manager, name):
        self.manager = manager
        self.name = name

    def __get__(self, instance, cls=None):
        # Access to manager from class is fine:
        if instance is None:
            return self.manager

        # Check if there's a legitimate instance method we're hiding:
        try:
            hidden = getattr(super(Item, cls), self.name)
        except AttributeError:
            pass
        else:
            # Bind and return hidden method:
            return hidden.__get__(instance, cls)

        # Let them know they're wrong:
        cls_name = getattr(cls, '__name__', '')
        raise AttributeError("Manager isn't accessible via {}instances"
                             .format(cls_name + ' ' if cls_name else cls_name))


class ItemField(object):

    internal = None

    def __init__(self, **kws):
        self.kws = kws

    def make_internal(self, name):
        return self.internal(name=name, **self.kws)


class HashKeyField(ItemField):

    internal = fields.HashKey


class RangeKeyField(ItemField):

    internal = fields.RangeKey


class IncludeIndexField(ItemField):

    internal = fields.IncludeIndex


class DeclarativeItemBase(type):

    def __new__(mcs, name, bases, attrs):
        # Check that this is not the base class:
        if not any(isinstance(base, DeclarativeItemBase) for base in bases):
            return super(DeclarativeItemBase, mcs).__new__(mcs, name, bases, attrs)

        # Collect field and manager declarations from class definition:
        item_fields, managers = {}, {}
        for key, value in attrs.items():
            if isinstance(value, ItemField):
                item_fields[key] = attrs.pop(key)
            elif isinstance(value, ItemManager):
                managers[key] = value
            elif key == 'Meta' and isinstance(value, type):
                attrs['_meta'] = attrs.pop(key)

        # Ensure meta:
        if '_meta' not in attrs:
            attrs['_meta'] = type('Meta', (object,), {})

        # Hold onto field declarations:
        attrs['_meta'].fields = item_fields

        # Ensure manager:
        if 'items' not in managers:
            # Set default manager:
            managers['items'] = ItemManager()
        for manager_name, manager in managers.items():
            attrs[manager_name] = ItemManagerDescriptor(manager, name=manager_name)

        return super(DeclarativeItemBase, mcs).__new__(mcs, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        # Check that this is not the base class:
        if not any(isinstance(base, DeclarativeItemBase) for base in bases):
            super(DeclarativeItemBase, cls).__init__(name, bases, attrs)
            return

        # Ensure managers set up with reference to table (and class):
        default_name = name.lower() + ('s' if not name.endswith('s') else '')
        table_name = getattr(cls._meta, 'table_name', default_name)
        internal_fields = [field.make_internal(field_name)
                           for field_name, field in cls._meta.fields.items()]
        schema = [field for field in internal_fields
                  if isinstance(field, fields.BaseSchemaField)]
        indexes = [field for field in internal_fields
                   if isinstance(field, fields.BaseIndexField)]
        item_table = Table(
            table_name=db._table_name(table_name),
            schema=schema,
            indexes=indexes,
            connection=db.connection,
            item=cls,
        )
        for value in attrs.values():
            if isinstance(value, ItemManagerDescriptor) and value.manager.table is None:
                value.manager.table = item_table

        super(DeclarativeItemBase, cls).__init__(name, bases, attrs)


class Item(items.Item):

    __metaclass__ = DeclarativeItemBase

    def __init__(self, data=None, loaded=False):
        table = type(self).items.table
        super(Item, self).__init__(table, data, loaded)

    def __repr__(self):
        pk = self.pk
        keys = ', '.join(unicode(key) for key in pk)
        if len(pk) > 1:
            keys = "({})".format(keys)
        return "<{name}: {keys}>".format(name=self.__class__.__name__, keys=keys)

    @property
    def pk(self):
        return tuple(self.get_keys().values())

    def _remove_null_values(self):
        considered_types = (basestring, set, tuple, list, dict, types.NoneType)
        for key, value in self.items():
            if isinstance(value, considered_types) and not value:
                del self[key]
                self._orig_data.pop(key, None)

    def partial_save(self):
        if self.needs_save():
            # Always set "updated" time:
            self['updated'] = db.epoch_now()

            # Changing a value to something NULL-y has special meaning for
            # partial_save() -- it is treated as a deletion directive.
            # We don't *think* we want this, ever; we can always delete the key
            # explicitly. So, remove NULL-y values:
            self._remove_null_values()

        return super(Item, self).partial_save()

    def save(self, overwrite=False):
        if self.needs_save() or overwrite:
            # Always set "updated" time:
            self['updated'] = db.epoch_now()
        return super(Item, self).save(overwrite)
