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

    # Extended fields
    activities = ItemField()
    affiliations = ItemField()
    books = ItemField()
    devices = ItemField()
    friend_request_count = ItemField()
    has_timeline = ItemField()
    interests = ItemField()
    languages = ItemField()
    likes_count = ItemField()
    movies = ItemField()
    music = ItemField()
    political = ItemField()
    profile_update_time = ItemField()
    quotes = ItemField()
    relationship_status = ItemField()
    religion = ItemField()
    sports = ItemField()
    tv = ItemField()
    wall_count = ItemField()
