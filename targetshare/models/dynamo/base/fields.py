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

    def decode(self, value):
        try:
            decoder = self.kws['data_type'].decode
        except (KeyError, AttributeError):
            return value
        else:
            return decoder(value)


class HashKeyField(ItemField):

    internal = fields.HashKey


class RangeKeyField(ItemField):

    internal = fields.RangeKey
