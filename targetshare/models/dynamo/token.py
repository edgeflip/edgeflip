from .base import Item, ItemField, HashKeyField, RangeKeyField, NUMBER, DATETIME


class Token(Item):

    fbid = HashKeyField(data_type=NUMBER)
    appid = RangeKeyField(data_type=NUMBER)
    expires = ItemField(data_type=DATETIME)
    token = ItemField()
