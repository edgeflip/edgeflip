from faraday import (
    Item,
    ItemField,
    ItemLinkField,
    HashKeyField,
    RangeKeyField,
    NUMBER,
    DATETIME,
)


class Token(Item):

    fbid = HashKeyField(data_type=NUMBER)
    appid = RangeKeyField(data_type=NUMBER)
    expires = ItemField(data_type=DATETIME)
    token = ItemField()
    api = ItemField(data_type=NUMBER)

    user = ItemLinkField('User', db_key=fbid)
