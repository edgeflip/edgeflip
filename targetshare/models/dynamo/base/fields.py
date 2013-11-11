from boto.dynamodb2 import fields as basefields

from . import types


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


class ItemField(object):

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
