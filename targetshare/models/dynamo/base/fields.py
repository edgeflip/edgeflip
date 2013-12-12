from boto.dynamodb2 import fields as basefields

from . import loading, types


class UpsertStrategy(object):

    @staticmethod
    def overwrite(obj, key, value):
        obj[key] = value

    @staticmethod
    def combine(obj, key, value):
        obj[key] += value

    @staticmethod
    def dict_update(obj, key, value):
        dict_ = obj[key]
        if dict_:
            dict_.update(value)
        else:
            obj[key] = value


class BaseItemField(object):
    pass


class ItemField(BaseItemField):

    internal = None

    def __init__(self,
                 data_type=types.STRING,
                 upsert_strategy=UpsertStrategy.overwrite,
                 **kws):
        self.data_type = data_type
        self.upsert_strategy = upsert_strategy
        self.kws = kws

    def __repr__(self):
        dict_ = vars(self).copy()
        kws = dict_.pop('kws')
        dict_.update(kws)
        return "{}({})".format(
            type(self).__name__,
            ', '.join("{}={!r}".format(key, value) for key, value in dict_.items())
        )

    def make_internal(self, name):
        return self.internal and self.internal(name=name,
                                               data_type=self.data_type,
                                               **self.kws)

    def decode(self, value):
        if isinstance(self.data_type, types.DataType):
            return self.data_type.decode(value)
        return value


class HashKeyField(ItemField):

    internal = basefields.HashKey


class RangeKeyField(ItemField):

    internal = basefields.RangeKey


class ItemLinkField(BaseItemField):
    """Item field indicating a link between two Items, similar to a foreign key."""

    Unset = object()

    def __init__(self, item, db_key, linked_name=Unset):
        self.item = item
        if isinstance(db_key, (tuple, list)):
            self.db_key = db_key
        else:
            self.db_key = (db_key,)
        self.linked_name = linked_name

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ', '.join("{}={!r}".format(key, value)
                      for (key, value) in vars(self).items())
        )

    def resolve_link(self, item):
        self.item = item

    def link(self, reverse_descriptor=None):
        """Resolve item reference or connect listener to resolve reference once
        the Item exists.

        Optionally accepts a ReverseLinkFieldProperty, so as to give it the same
        treatment.

        """
        item = self.item
        if isinstance(item, basestring):
            try:
                item = loading.cache[item]
            except KeyError:
                pending = loading.pending_links[item]
                pending.add(self)
                if reverse_descriptor:
                    pending.add(reverse_descriptor)
                return

        self.resolve_link(item)
        if reverse_descriptor:
            reverse_descriptor.resolve_link(item)

    @staticmethod
    def cache_name(name):
        return '_{}_cache'.format(name)

    @classmethod
    def cache_get(cls, name, instance):
        return getattr(instance, cls.cache_name(name), None)

    @classmethod
    def cache_set(cls, name, instance, value):
        setattr(instance, cls.cache_name(name), value)

    @classmethod
    def cache_clear(cls, name, instance):
        try:
            delattr(instance, cls.cache_name(name))
        except AttributeError:
            pass
