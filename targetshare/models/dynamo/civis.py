from faraday import Item, ItemField, HashKeyField, JSON, NUMBER


class CivisResult(Item):

    fbid = HashKeyField(data_type=NUMBER)
    result = ItemField(data_type=JSON)
