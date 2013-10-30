from .base import Item, ItemField, HashKeyField, NUMBER


class CivisResult(Item):

    fbid = HashKeyField(data_type=NUMBER)
    score_json = ItemField()
