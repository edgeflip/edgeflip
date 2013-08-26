from boto.dynamodb2 import fields


class ItemField(object):

    internal = None

    def __init__(self, **kws):
        self.kws = kws

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ', '.join("{}={!r}".format(key, value) for key, value in self.kws.items())
        )

    def make_internal(self, name):
        return self.internal and self.internal(name=name, **self.kws)

    def validate(self, value):
        try:
            validator = self.kws['data_type'].validate
        except (KeyError, AttributeError):
            pass
        else:
            validator(value)

    def load(self, value):
        try:
            loader = self.kws['data_type'].load
        except (KeyError, AttributeError):
            return value
        else:
            return loader(value)


class HashKeyField(ItemField):

    internal = fields.HashKey


class RangeKeyField(ItemField):

    internal = fields.RangeKey
