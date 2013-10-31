"""Extension to the boto Item and framework for the class-based definition of
DynamoDB tables and documents.

"""
import itertools
import re

from boto.dynamodb2 import fields as basefields, items as baseitems
from django.dispatch import Signal
from django.utils import timezone

from .fields import ItemField
from .manager import ItemManager, ItemManagerDescriptor
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
    indexes = ()
    table_name = None # Defaults to lowercased, pluralized version of class name

    # "Hide" methods with "__ __" to avoid appearance of available options #

    @classmethod
    def __isoption__(cls, key):
        """Return whether the given key is a valid configuration option."""
        return not cls.__isoption__.hidden.match(key) and key in vars(cls)
    __isoption__.__func__.hidden = re.compile(r'^__.*__$')

    @classmethod
    def __user__(cls, name, fields, user):
        """Build a new Meta instance from class declaration information and the
        user metadata class (if supplied).

        """
        meta = cls(name, fields)
        if user:
            vars(meta).update((key, value) for key, value in vars(user).items()
                              if cls.__isoption__(key))
        return meta

    def __init__(self, name, fields):
        self.table_name = name.lower() + ('s' if not name.endswith('s') else '')
        self.fields = fields

    @property
    def __merged__(self):
        """View of metadata, which are based on instance attribute retrieval, built
        by merging instance attribute dict on top of class attribute dict.

        """
        return dict(itertools.chain(
            # Defaults:
            ((key, value) for key, value in vars(type(self)).items() if self.__isoption__(key)),
            # User specifications:
            vars(self).items()
        ))

    def __repr__(self):
        return "<{}({})>".format(
            type(self).__name__,
            ", ".join("{}={!r}".format(key, value) for key, value in self.__merged__.items())
        )


class ItemDoesNotExist(LookupError):
    pass


# No need to depend on Django, but as long as we have access to
# their signal/receiver implementation...:
item_declared = Signal(providing_args=["item"])


class FieldProperty(object):
    """Item field property descriptor, allowing access to the item data dictionary
    via the attribute interface.

    By applying these to the Item definition, its attribute interface may be
    preferred, and e.g. typos will raise AttributeError rather than simply returning
    None.

    """
    def __init__(self, field_name):
        self.field_name = field_name

    def __get__(self, instance, cls=None):
        return self if instance is None else instance[self.field_name]

    def __set__(self, instance, value):
        instance[self.field_name] = value

    def __delete__(self, instance):
        del instance[self.field_name]

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.field_name)


class DeclarativeItemBase(type):
    """Metaclass which defines subclasses of Item based on their declarations."""
    update_field = 'updated'

    def __new__(mcs, name, bases, attrs):
        # Check that this is not the base class:
        if not any(isinstance(base, DeclarativeItemBase) for base in bases):
            return super(DeclarativeItemBase, mcs).__new__(mcs, name, bases, attrs)

        # Set class defaults:
        attrs.setdefault('items', ItemManager())
        if mcs.update_field:
            attrs.setdefault(mcs.update_field, ItemField(data_type=DATETIME))

        # Collect field declarations from class defn, set field properties and wrap managers:
        item_fields = {}
        for key, value in attrs.items():
            if isinstance(value, ItemField):
                item_fields[key] = value
                attrs[key] = FieldProperty(key)
            elif isinstance(value, ItemManager):
                attrs[key] = ItemManagerDescriptor(value, name=key)

        # Set meta:
        attrs['_meta'] = Meta.__user__(name, item_fields, attrs.pop('Meta', None))

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
        item_table = Table(
            table_name=cls._meta.table_name,
            item=cls,
            schema=schema,
            indexes=cls._meta.indexes,
        )
        for value in attrs.values():
            if isinstance(value, ItemManagerDescriptor) and value.manager.table is None:
                value.manager.table = item_table

        super(DeclarativeItemBase, cls).__init__(name, bases, attrs)

        # Notify listeners:
        item_declared.send(sender=cls)


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
    get_dynamizer = Dynamizer

    def __init__(self, data=None, loaded=False, **kwdata):
        data = {} if data is None else dict(data)
        data.update(kwdata)

        # Clean data before populating it
        data = {key: self._pre_set(key, value) for (key, value) in data.items()}

        table = type(self).items.table
        super(Item, self).__init__(table, data, loaded)
        self._dynamizer = self.get_dynamizer()

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
        """Clean exotic types (e.g. DATE)."""
        field = self._meta.fields.get(key)
        if field:
            value = field.decode(value)
        elif not self._meta.allow_undeclared_fields:
            raise TypeError("Field {!r} undeclared and unallowed by {} items"
                            .format(key, type(self).__name__))
        return value

    def __setitem__(self, key, value):
        value = self._pre_set(key, value)
        super(Item, self).__setitem__(key, value)

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
