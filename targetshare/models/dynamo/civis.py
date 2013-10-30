from .base import Item, ItemField, HashKeyField, NUMBER, JSON


class CivisResult(Item):

    fbid = HashKeyField(data_type=NUMBER)
    result = ItemField(data_type=JSON)
