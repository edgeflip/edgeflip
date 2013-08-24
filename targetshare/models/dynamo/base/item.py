"""Extension to the boto Item and framework for the class-based definition of
DynamoDB tables and documents.

"""
from __future__ import absolute_import
import itertools

from boto.dynamodb2 import fields as basefields, items as baseitems
from django.utils import timezone

from targetshare.models.dynamo import db, utils

from .fields import ItemField
from .table import Table
from .types import DATETIME, Dynamizer, is_null


# Define framework for the definition of dynamo tables and #
# data interactions around (an extension of) the boto Item #


class Meta(object):
    """Item definition metadata.

    >>> meta = Meta('Name', [FIELD, ...]) # doctest: +IGNORE
    >>> meta.table_name
    'names'

    """
    # User-available options:
    allow_undeclared_fields = False
    table_name = None # Defaults to lowercased, pluralized version of class name

    # "Hide" methods with "_" to avoid appearance of available options #

    @classmethod
    def _from_user(cls, name, fields, user):
        """Build a new Meta instance from class declaration information and the
        user metadata class (if supplied).

        """
        meta = cls(name, fields)
        if user:
            vars(meta).update((key, value) for key, value in vars(user).items()
                              if key in vars(cls) and not key.startswith('_'))
        return meta

    def __init__(self, name, fields):
        self.table_name = name.lower() + ('s' if not name.endswith('s') else '')
        self.fields = fields

    @property
    def _merged(self):
        """View of metadata, which are based on instance attribute retrieval, built
        by merging instance attribute dict on top of class attribute dict.

        """
        return dict(itertools.chain(
            # Defaults:
            ((key, value) for key, value in vars(type(self)).items()
             if not key.startswith('_')),
            # User specifications:
            vars(self).items()
        ))

    def __repr__(self):
        return "<{}({})>".format(
            type(self).__name__,
            ", ".join("{}={!r}".format(key, value) for key, value in self._merged.items())
        )


class ItemDoesNotExist(LookupError):
    pass


class DeclarativeItemBase(type):
    """Metaclass which defines subclasses of Item based on their declarations."""
    update_field = 'updated'

    def __new__(mcs, name, bases, attrs):
        # Check that this is not the base class:
        if not any(isinstance(base, DeclarativeItemBase) for base in bases):
            return super(DeclarativeItemBase, mcs).__new__(mcs, name, bases, attrs)

        # Collect field, manager and options declarations from class definition:
        user_meta = None
        item_fields, managers = {}, {}
        for key, value in attrs.items():
            if isinstance(value, ItemField):
                item_fields[key] = attrs.pop(key)
            elif isinstance(value, ItemManager):
                managers[key] = value
            elif key == 'Meta' and isinstance(value, type):
                user_meta = attrs.pop(key)

        # Ensure manager:
        if 'items' not in managers:
            # Set default manager:
            managers['items'] = ItemManager()
        for manager_name, manager in managers.items():
            attrs[manager_name] = ItemManagerDescriptor(manager, name=manager_name)

        # Ensure update field:
        if mcs.update_field and mcs.update_field not in item_fields:
            item_fields[mcs.update_field] = ItemField(data_type=DATETIME)

        # Set meta:
        attrs['_meta'] = Meta._from_user(name, item_fields, user=user_meta)

        # Set Item-specific ItemDoesNotExist:
        attrs['DoesNotExist'] = type('DoesNotExist', (ItemDoesNotExist,), {})

        return super(DeclarativeItemBase, mcs).__new__(mcs, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        # Check that this is not the base class:
        if not any(isinstance(base, DeclarativeItemBase) for base in bases):
            super(DeclarativeItemBase, cls).__init__(name, bases, attrs)
            return

        # Ensure managers set up with reference to table (and class):
        internal_fields = [field.make_internal(field_name)
                           for field_name, field in cls._meta.fields.items()]
        schema = [field for field in internal_fields
                  if isinstance(field, basefields.BaseSchemaField)]
        indexes = [field for field in internal_fields
                   if isinstance(field, basefields.BaseIndexField)]
        item_table = Table(
            table_name=db.table_name(cls._meta.table_name),
            schema=schema,
            indexes=indexes,
            connection=db.connection,
            item=cls,
        )
        # Keep record of table:
        utils.database.tables.add(item_table)

        for value in attrs.values():
            if isinstance(value, ItemManagerDescriptor) and value.manager.table is None:
                value.manager.table = item_table

        super(DeclarativeItemBase, cls).__init__(name, bases, attrs)


class Item(baseitems.Item):
    """Extention to the boto Item, allowing for definition of Table schema, additional
    field-level validation and data conversion, and table-specific objectification.

    Items and their Tables may be defined as simply as::

        class User(Item):

            username = HashKeyField(data_type=NUMBER)

    and then their tables interacted with as::

        User.items.get_item(username='johndoe')

    The default item "manager" may be overridden, additional managers specified, and
    Item options may be defined via a `Meta` class::

        class User(Item):

            username = HashKeyField(data_type=NUMBER)

            items = MyItemManager()
            fancyitems = MyFancyItemManager()

            class Meta(object):
                allow_undeclared_fields = True

    """
    __metaclass__ = DeclarativeItemBase

    @classmethod
    def from_boto(cls, item):
        """Convert a boto Item newly loaded from DynamoDB to Item."""
        new = cls(dict(item), loaded=True)
        new._post_load()
        return new

    def __init__(self, data=None, loaded=False):
        if data:
            # Validate data before populating it
            for key, value in data.items():
                self._pre_set(key, value)

        table = type(self).items.table
        super(Item, self).__init__(table, data, loaded)
        self._dynamizer = Dynamizer()

    def __repr__(self):
        pk = self.pk
        keys = ', '.join(unicode(key) for key in pk)
        if len(pk) > 1:
            keys = "({})".format(keys)
        return "<{name}: {keys}>".format(name=self.__class__.__name__, keys=keys)

    @property
    def pk(self):
        """The Item's signature in key-less, hashable form."""
        return tuple(self.get_keys().values())

    def _pre_set(self, key, value):
        """Validate exotic types (e.g. DATE)."""
        field = self._meta.fields.get(key)
        if field:
            field.validate(value)
        elif not self._meta.allow_undeclared_fields:
            raise TypeError("Field {!r} undeclared and unallowed by {} items"
                            .format(key, type(self).__name__))

    def __setitem__(self, key, value):
        self._pre_set(key, value)
        super(Item, self).__setitem__(key, value)

    def load(self, data):
        super(Item, self).load(data)
        self._post_load()

    def _post_load(self):
        """Check for exotic datatypes to convert further."""
        for key, value in self.items():
            field = self._meta.fields.get(key)
            if not field:
                continue
            self[key] = self._orig_data[key] = field.load(value)

    # prepare_full determines data to put for save and BatchTable once they
    # know there's data to put. Insert timestamp for update:
    def prepare_full(self):
        if type(self).update_field:
            # Always set "updated" time:
            self[type(self).update_field] = timezone.now()
        return super(Item, self).prepare_full()

    def _remove_null_values(self):
        for key, value in self.items():
            if is_null(value):
                del self[key]
                self._orig_data.pop(key, None)

    # partial_save's prepare_partial isn't the same sort of hook as
    # prepare_full. Perform data preparations directly:
    def partial_save(self):
        if self.needs_save():
            if type(self).update_field:
                # Always set updated time:
                self[type(self).update_field] = timezone.now()

            # Changing a value to something NULL-y has special meaning for
            # partial_save() -- it is treated as a deletion directive.
            # We don't *think* we want this, ever; we can always delete the key
            # explicitly. So, remove NULL-y values:
            self._remove_null_values()

        return super(Item, self).partial_save()


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
