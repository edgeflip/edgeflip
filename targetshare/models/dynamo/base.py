from boto.dynamodb2 import fields, results, table, items

from . import db


# Subclass boto's results classes to prevent fetch_more from bailing
# when any one batch is empty.

# WARNING: Upgrading boto? Upgrade this too! #

# Start ResultSet patch #

# Note: for the time being, ResultSet is NOT used. See ItemManager.
class ResultSet(results.ResultSet):

    # Copy of ResultSet's fetch_more (except for %%):
    def fetch_more(self):
        """
        When the iterator runs out of results, this method is run to re-execute
        the callable (& arguments) to fetch the next page.

        Largely internal.
        """
        self._reset()

        args = self.call_args[:]
        kwargs = self.call_kwargs.copy()

        if self._last_key_seen is not None:
            kwargs[self.first_key] = self._last_key_seen

        results = self.the_callable(*args, **kwargs)

        # %% Comment out bail condition:
        #if not len(results.get('results', [])):
        #    self._results_left = False
        #    return
        # %% Instead just ensure response is well-formed:
        results.setdefault('results', [])

        self._results.extend(results['results'])
        self._last_key_seen = results.get('last_key', None)

        if self._last_key_seen is None:
            self._results_left = False

        # Decrease the limit, if it's present.
        if self.call_kwargs.get('limit'):
            self.call_kwargs['limit'] -= len(results['results'])
            # and if limit hits zero, we don't have any more
            # results to look for
            if 0 == self.call_kwargs['limit']:
                self._results_left = False


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

# End ResultSet patch #


class ItemManager(object):

    # Do NOT override base ResultSet yet. It seems to do the right thing:
    result_set = results.ResultSet

    # BatchGetResultSet is proven to be wrong. Override with patched version:
    batch_get_result_set = BatchGetResultSet

    def __init__(self, item=None, table=None, name='table'):
        self.item = item
        self.table = table
        self.name = name

    def _convert(self, instance):
        if isinstance(instance, results.BatchGetResultSet):
            kls = self.batch_get_result_set
        elif isinstance(instance, results.ResultSet):
            kls = self.result_set
        elif isinstance(instance, items.Item):
            kls = self.item
        else:
            return instance
        new = kls()
        new.__dict__ = instance.__dict__
        return new

    # Querying methods whose results must be converted #

    def query(self, *args, **kws):
        return self._convert(self.table.query(*args, **kws))

    def scan(self, *args, **kws):
        return self._convert(self.table.scan(*args, **kws))

    def batch_get(self, *args, **kws):
        return self._convert(self.table.batch_get(*args, **kws))

    # Simple proxies #

    def count(self):
        return self.table.count()


class ItemManagerDescriptor(object):

    def __init__(self, manager):
        self.manager = manager

    def __get__(self, instance, type=None):
        if instance is not None:
            name = getattr(type, '__name__', '')
            raise AttributeError("Manager isn't accessible via {}instances"
                                 .format(name + ' ' if name else name))
        return self.manager

    def __set__(self, instance, value):
        if isinstance(value, table.Table):
            self.manager.table = value
        else:
            setattr(instance, self.manager.name, value)


class Field(object):

    internal = None

    def __init__(self, **kws):
        self.kws = kws

    def make_internal(self, name):
        return self.internal(name=name, **self.kws)


class HashKeyField(Field):

    internal = fields.HashKey


class RangeKeyField(Field):

    internal = fields.RangeKey


class IncludeIndexField(Field):

    internal = fields.IncludeIndex


class DeclarativeItemBase(type):

    def __new__(mcs, name, bases, attrs):
        # Check that is concrete class:
        if attrs.get('_abstract'):
            return super(DeclarativeItemBase, mcs).__new__(mcs, name, bases, attrs)

        # Override inherited abstract declaration:
        attrs['_abstract'] = False

        # Collect field and manager declarations from class definition:
        item_fields = []
        managers = {}
        for key, value in attrs.items():
            if isinstance(value, Field):
                field = value.make_internal(key)
                item_fields.append(field)
                del attrs[key]
            elif isinstance(value, ItemManager):
                managers[key] = value
            elif key == 'Meta' and isinstance(value, type):
                attrs['_meta'] = value
                del attrs[key]

        # Ensure meta, manager and table:
        meta = attrs.setdefault('_meta', type('Meta', (object,), {}))
        default_name = name.lower() + ('s' if not name.endswith('s') else '')
        table_name = getattr(meta, 'table_name', default_name)
        item_table = table.Table(
            table_name=db._table_name(table_name),
            schema=[field for field in item_fields if isinstance(field, fields.BaseSchemaField)],
            indexes=[field for field in item_fields if isinstance(field, fields.BaseIndexField)],
            connection=db.connection,
        )
        if 'table' not in managers:
            # Set default manager:
            managers['table'] = ItemManager(item=None, table=None)
        for manager_name, manager in managers.items():
            if manager.table is None:
                manager.table = item_table
            attrs[manager_name] = ItemManagerDescriptor(manager)

        return super(DeclarativeItemBase, mcs).__new__(mcs, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        # Ensure managers set up with reference to class:
        for key, value in attrs.items():
            if isinstance(value, ItemManagerDescriptor) and value.manager.item is None:
                value.manager.item = cls
        super(DeclarativeItemBase, cls).__init__(name, bases, attrs)


class Item(items.Item):

    __metaclass__ = DeclarativeItemBase
    _abstract = True
