"""Extension to the boto Item and framework for the class-based definition of
DynamoDB tables and documents.

"""
import itertools

from boto.dynamodb2 import fields as basefields, items as baseitems
from django.utils import timezone

from . import loading
from . import manager as managers
from . import types
from .fields import ItemField, ItemLinkField
from .table import Table
from .utils import cached_property

from targetshare import utils


# Define framework for the definition of dynamo tables and #
# data interactions around (an extension of) the boto Item #


class Meta(object):
    """Item definition metadata.

    >>> meta = Meta('Name', [FIELD, ...]) # doctest: +IGNORE
    >>> meta.table_name
    'names'

    """
    # User-available options & default values
    DEFAULTS = dict(
        allow_undeclared_fields=False,
        undeclared_data_type=None,
        indexes=(),
        app_name=None,

        # Defaults to lowercased, pluralized version of class name:
        table_name=None,
    )

    def __init__(self, name, keys, links, user=None):
        # Set options:
        vars(self).update(self.DEFAULTS)
        if user:
            vars(self).update(
                (key, value) for (key, value) in vars(user).items()
                if not key.startswith('__')
            )

        self.item_name = name
        if not self.table_name:
            self.table_name = utils.camel_to_underscore(name)
            if not self.table_name.endswith('s'):
                self.table_name += 's'
            if self.app_name:
                self.table_name = '.'.join([self.app_name, self.table_name])

        self.keys = keys
        self.links = links

        self.fields = links.copy()
        self.fields.update(keys)

        self.link_keys = {}
        for (link_name, link_field) in links.items():
            for db_key_item in link_field.db_key:
                self.link_keys[db_key_item] = link_name

    @property
    def signed(self):
        return '.'.join(part for part in [self.app_name, self.item_name] if part)

    def __repr__(self):
        return "<{}: {}>".format(type(self).__name__, self.signed)


class ItemDoesNotExist(LookupError):
    pass


class MultipleItemsReturned(LookupError):
    pass


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


class BaseFieldProperty(object):

    def __init__(self, field_name):
        self.field_name = field_name

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.field_name)


class FieldProperty(BaseFieldProperty):
    """Item field property descriptor, allowing access to the item data dictionary
    via the attribute interface.

    By applying these to the Item definition, its attribute interface may be
    preferred, and e.g. typos will raise AttributeError rather than simply returning
    None.

    """
    def __get__(self, instance, cls=None):
        return self if instance is None else instance.get(self.field_name)

    def __set__(self, instance, value):
        instance[self.field_name] = value

    def __delete__(self, instance):
        del instance[self.field_name]


class LinkFieldProperty(BaseFieldProperty):
    """Item link field descriptor, providing management of a linked Item."""

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        field = instance._meta.links[self.field_name]
        result = field.cache_get(self.field_name, instance)
        if result is not None:
            return result

        try:
            manager = field.item.items
        except AttributeError:
            raise TypeError("Item link unresolved or bad link argument: {!r}"
                            .format(field.item))

        keys = manager.table.get_key_fields()
        try:
            values = field.get_item_pk(instance)
        except KeyError:
            return None

        query = dict(zip(keys, values))
        result = manager.get_item(**query)
        field.cache_set(self.field_name, instance, result)
        return result

    def __set__(self, instance, related):
        field = instance._meta.links[self.field_name]
        for (key, value) in zip(field.db_key, related.pk):
            instance[key] = value
        field.cache_set(self.field_name, instance, related)

    def __delete__(self, instance):
        field = instance._meta.links[self.field_name]
        for key in field.db_key:
            del instance[key]
        field.cache_clear(self.field_name, instance)


class ReverseLinkFieldProperty(BaseFieldProperty):
    """The Item link field's reversed descriptor, providing access to all Items with
    matching links.

    """
    def __init__(self, field_name, item_name, link_field):
        super(ReverseLinkFieldProperty, self).__init__(field_name)
        self.item_name = item_name
        self.link_field = link_field

    def resolve_link(self, parent):
        if hasattr(parent, self.field_name):
            raise ValueError("{} already defines attribute {}"
                             .format(parent.__name__, self.field_name))
        setattr(parent, self.field_name, self)

    @cached_property
    def linked_manager_cls(self):
        # FIXME: Inheriting from a distinct BaseItemManager allows us to limit
        # FIXME: interface to only querying methods; but, this disallows inheritance
        # FIXME: of user-defined ItemManager methods...
        child_meta = self.item._meta
        link_field = self.link_field
        db_key = link_field.db_key

        class LinkedItemQuery(managers.AbstractLinkedItemQuery):

            name_child = child_meta.link_keys[db_key[0]]
            child_field = child_meta.links[name_child]

        class LinkedItemManager(managers.AbstractLinkedItemManager):

            core_filters = tuple("{}__eq".format(key) for key in db_key)
            query_cls = LinkedItemQuery

        return LinkedItemManager

    @cached_property
    def item(self):
        try:
            return loading.cache[self.item_name]
        except KeyError:
            raise TypeError("Item link unresolved or bad link argument: {!r}"
                            .format(self.item_name))

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        manager = self.linked_manager_cls(self.item.items.table, instance)
        # NOTE: If ReverseLinkFieldProperty ever supports __set__ et al, below
        # caching method won't work (it will be a data descriptor and take
        # precendence over instance __dict__). (See LinkFieldProperty.)
        vars(instance)[self.field_name] = manager
        return manager


class DeclarativeItemBase(type):
    """Metaclass which defines subclasses of Item based on their declarations."""
    update_field = 'updated'

    def __new__(mcs, name, bases, attrs):
        # Check that this is not the base class:
        if not any(isinstance(base, DeclarativeItemBase) for base in bases):
            return super(DeclarativeItemBase, mcs).__new__(mcs, name, bases, attrs)

        # Set class defaults:
        attrs.setdefault('items', managers.ItemManager())
        if mcs.update_field:
            attrs.setdefault(mcs.update_field, ItemField(data_type=types.DATETIME))

        # Collect field declarations from class defn, set field properties and wrap managers:
        item_fields, link_fields, field_keys = {}, {}, {}
        for key, value in attrs.items():
            if isinstance(value, ItemField):
                item_fields[key] = value
                # Store reverse for ItemLinkField.db_key:
                field_keys[value] = key
                attrs[key] = FieldProperty(key)
            elif isinstance(value, ItemLinkField):
                # Resolve ItemField references:
                value.db_key = tuple(
                    field_keys[key_ref] if isinstance(key_ref, ItemField) else key_ref
                    for key_ref in value.db_key
                )
                link_fields[key] = value
                attrs[key] = LinkFieldProperty(key)
            elif isinstance(value, managers.ItemManager):
                attrs[key] = ItemManagerDescriptor(value, name=key)

        # Set meta:
        meta = attrs['_meta'] = Meta(name, item_fields, link_fields, attrs.pop('Meta', None))

        # Resolve links:
        for link_field in link_fields.values():
            # Construct linked item manager property:
            linked_name = link_field.linked_name
            if linked_name:
                if linked_name is link_field.Unset:
                    linked_name = utils.camel_to_underscore(name).replace('_', '')
                    if linked_name.endswith('s'):
                        linked_name += '_set'
                    else:
                        linked_name += 's'
                reverse_link = ReverseLinkFieldProperty(linked_name, meta.signed, link_field)
            else:
                reverse_link = None
            link_field.link(reverse_descriptor=reverse_link)

        # Set Item-specific ItemDoesNotExist:
        attrs['DoesNotExist'] = type('DoesNotExist', (ItemDoesNotExist,), {})
        attrs['MultipleItemsReturned'] = type('MultipleItemsReturned', (MultipleItemsReturned,), {})

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
        loading.item_declared.send(sender=cls)


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

        # Clean data before populating it and gather links
        clean_data = {}
        linked_data = []
        for (key, value) in data.items():
            if key in self._meta.links:
                if loaded:
                    # Allowing this would cause weird issues with _orig_data,
                    # (and wouldn't make sense anyway):
                    raise TypeError("Items loaded from database cannot populate link fields")
                linked_data.append((key, value))
            else:
                clean_data[key] = self._pre_set(key, value)

        table = type(self).items.table
        super(Item, self).__init__(table, clean_data, loaded)
        self._dynamizer = self.get_dynamizer()

        # Apply linked objects
        for (key, value) in linked_data:
            setattr(self, key, value)

    def __repr__(self):
        pk = self.pk
        keys = ', '.join(unicode(key) for key in pk)
        if len(pk) > 1:
            keys = "({})".format(keys)
        return "<{name}: {keys}>".format(name=self.__class__.__name__, keys=keys)

    def __getstate__(self):
        """Return the Item object state for pickling."""
        # It's probably worthwhile for ReverseLinkFieldProperty to cache
        # LinkedItemManagers on the instance; but, not worthwhile, for the time
        # being anyway, to support pickling of instances of these manufactured
        # classes.
        return {key: value for (key, value) in vars(self).items()
                if not isinstance(value, managers.AbstractLinkedItemManager)}

    @property
    def pk(self):
        """The Item's signature in key-less, hashable form."""
        return tuple(self.get_keys().values())

    @property
    def document(self):
        """The Item's data excluding its signature."""
        meta_fields = set(itertools.chain(self.table.get_key_fields(),
                                          [type(self).update_field]))
        return {key: value for (key, value) in self.items()
                if key not in meta_fields}

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.pk == other.pk

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(tuple(self.get_keys().items()))

    def __getitem__(self, key):
        # boto's Item[key] is really Item.get(key), but this causes various
        # problems, and only makes sense for __getitem__ when undeclared fields
        # are allowed:
        if self._meta.allow_undeclared_fields:
            return self._data.get(key)

        # We provide a field property interface to do Item.get(key); there's
        # no need to lie about our underlying data:
        return self._data[key]

    @classmethod
    def _pre_set(cls, key, value):
        """Clean exotic types (e.g. DATE)."""
        key_field = cls._meta.keys.get(key)
        if key_field:
            return key_field.decode(value)

        link_field = cls._meta.links.get(key)
        if link_field:
            raise TypeError("Access to {!r} required through descriptor"
                            .format(link_field))

        if not cls._meta.allow_undeclared_fields:
            raise TypeError("Field {!r} undeclared and unallowed by {} items"
                            .format(key, cls.__name__))

        if isinstance(cls._meta.undeclared_data_type, types.DataType):
            return cls._meta.undeclared_data_type.decode(value)

        return value

    def _clear_link_cache(self, key):
        try:
            link_name = self._meta.link_keys[key]
        except KeyError:
            return
        link_field = self._meta.links[link_name]
        link_field.cache_clear(link_name, self)

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
