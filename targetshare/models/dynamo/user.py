from boto.dynamodb2 import types

from . import base


class User(base.Item):

    fbid = base.HashKeyField(data_type=types.NUMBER)
