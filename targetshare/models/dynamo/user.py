from .base import Item, ItemField, HashKeyField, NUMBER, DATETIME


class User(Item):

    fbid = HashKeyField(data_type=NUMBER)
    birthday = ItemField(data_type=DATETIME)
    fname = ItemField()
    lname = ItemField()
    email = ItemField()
    gender = ItemField()
    city = ItemField()
    state = ItemField()
