from .base import (
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

    user = ItemLinkField('User', db_key=fbid)
