"""Extension to the boto Item and framework for the class-based definition of
DynamoDB tables and documents.

"""
import itertools
import re

from boto.dynamodb2 import fields as basefields, items as baseitems
from django.dispatch import Signal
from django.utils import timezone

from . import types
from .fields import ItemField, ItemLinkField
from .manager import ItemManager, ItemManagerDescriptor
from .table import Table

from targetshare import utils


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
    undeclared_data_type = None
    indexes = ()
    table_name = None # Defaults to lowercased, pluralized version of class name

    # "Hide" methods with "__ __" to avoid appearance of available options #

    @classmethod
    def __isoption__(cls, key):
        """Return whether the given key is a valid configuration option."""
        return not cls.__isoption__.hidden.match(key) and key in vars(cls)
    __isoption__.__func__.hidden = re.compile(r'^__.*__$')

    @classmethod
    def __user__(cls, name, keys, links, user):
        """Build a new Meta instance from class declaration information and the
        user metadata class (if supplied).

        """
        meta = cls(name, keys, links)
        if user:
            vars(meta).update((key, value) for key, value in vars(user).items()
                              if cls.__isoption__(key))
        return meta

    def __init__(self, name, keys, links):
        self.table_name = utils.camel_to_underscore(name)
        if not self.table_name.endswith('s'):
            self.table_name += 's'

        self.keys = keys
        self.links = links

        self.fields = links.copy()
        self.fields.update(keys)

        self.link_keys = {}
        for (link_name, link_field) in links.items():
            for db_key_item in link_field.field.db_key:
                self.link_keys[db_key_item] = link_field

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


cache = {}


def populate_cache(sender, **_kws):
    cache[sender.__name__] = sender

item_declared.connect(populate_cache)


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
        return self if instance is None else instance.get(self.field_name)

    def __set__(self, instance, value):
        instance[self.field_name] = value

    def __delete__(self, instance):
        del instance[self.field_name]

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.field_name)


class BoundLinkField(object):

    pending_links = {}

    @classmethod
    def resolve_lazy(cls, sender, **_kws):
        for field in cls.pending_links.get(sender.__name__, ()):
            field.item = sender

    @classmethod
    def bind(cls, name, field, key_fields):
        if isinstance(field.item, basestring):
            try:
                item = cache[field.item]
            except KeyError:
                cls.pending_links.setdefault(field.item, set()).add(field)
            else:
                field.item = item

        field_keys = {item_field: key_name
                      for (key_name, item_field) in key_fields.items()}
        field.db_key = tuple(
            field_keys[key_ref] if isinstance(key_ref, ItemField) else key_ref
            for key_ref in field.db_key
        )

        return cls(name, field)

    def __init__(self, name, field):
        self.name = name
        self.field = field

    @property
    def cache_name(self):
        return '_{}_cache'.format(self.name)

    def cache_get(self, instance):
        return getattr(instance, self.cache_name, None)

    def cache_set(self, instance, value):
        setattr(instance, self.cache_name, value)

    def cache_clear(self, instance):
        try:
            delattr(instance, self.cache_name)
        except AttributeError:
            pass

    def __repr__(self):
        return "<{!r} bound at '{}'>".format(self.field, self.name)

item_declared.connect(BoundLinkField.resolve_lazy)


class LinkFieldProperty(object):

    def __init__(self, bound_field):
        self.bound_field = bound_field

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        result = self.bound_field.cache_get(instance)
        if result is not None:
            return result

        field = self.bound_field.field
        try:
            manager = field.item.items
        except AttributeError:
            raise TypeError("Item link unresolved or bad link argument: {!r}"
                            .format(field.item))

        keys = manager.table.get_key_fields()
        values = (instance[key] for key in field.db_key)
        try:
            query = dict(zip(keys, values))
        except KeyError:
            return None

        result = manager.get_item(**query)
        self.bound_field.cache_set(instance, result)
        return result

    def __set__(self, instance, related):
        for (key, value) in zip(self.bound_field.field.db_key, related.pk):
            instance[key] = value
        self.bound_field.cache_set(instance, related)

    def __delete__(self, instance):
        for key in self.bound_field.field.db_key:
            del instance[key]
        self.bound_field.cache_clear(instance)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.bound_field)


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
            attrs.setdefault(mcs.update_field, ItemField(data_type=types.DATETIME))

        # Collect field declarations from class defn, set field properties and wrap managers:
        item_fields, link_fields = {}, {}
        for key, value in attrs.items():
            if isinstance(value, ItemField):
                item_fields[key] = value
                attrs[key] = FieldProperty(key)
            elif isinstance(value, ItemLinkField):
                bound_link_field = BoundLinkField.bind(key, value, item_fields)
                link_fields[key] = bound_link_field
                attrs[key] = LinkFieldProperty(bound_link_field)
            elif isinstance(value, ItemManager):
                attrs[key] = ItemManagerDescriptor(value, name=key)

        # Set meta:
        attrs['_meta'] = Meta.__user__(name, item_fields, link_fields, attrs.pop('Meta', None))

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
                           for field_name, field in cls._meta.keys.items()]
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
    get_dynamizer = types.Dynamizer

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

    def __getitem__(self, key):
        # boto's Item[key] is really Item.get(key), but this causes various
        # problems, and only makes sense for __getitem__ when undeclared fields
        # are allowed:
        if self._meta.allow_undeclared_fields:
            return self._data.get(key)

        # We provide a field property interface to do Item.get(key); there's
        # no need to lie about our underlying data:
        return self._data[key]

    def _pre_set(self, key, value):
        """Clean exotic types (e.g. DATE)."""
        key_field = self._meta.keys.get(key)
        if key_field:
            return key_field.decode(value)

        link_field = self._meta.links.get(key)
        if link_field:
            raise TypeError("Access to {!r} required through descriptor"
                            .format(link_field))

        if not self._meta.allow_undeclared_fields:
            raise TypeError("Field {!r} undeclared and unallowed by {} items"
                            .format(key, type(self).__name__))

        if isinstance(self._meta.undeclared_data_type, types.DataType):
            return self._meta.undeclared_data_type.decode(value)

        return value

    def _clear_link_cache(self, key):
        try:
            link_field = self._meta.link_keys[key]
        except KeyError:
            pass
        else:
            link_field.cache_clear(self)

    def __setitem__(self, key, value):
        value = self._pre_set(key, value)
        self._clear_link_cache(key)
        super(Item, self).__setitem__(key, value)

    def __delitem__(self, key):
        self._clear_link_cache(key)
        super(Item, self).__delitem__(key)

    # prepare_full determines data to put for save and BatchTable once they
    # know there's data to put. Insert timestamp for update:
    def prepare_full(self):
        if type(self).update_field:
            # Always set "updated" time:
            self[type(self).update_field] = timezone.now()
        return super(Item, self).prepare_full()

    def _remove_null_values(self):
        for key, value in self.items():
            if types.is_null(value):
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
