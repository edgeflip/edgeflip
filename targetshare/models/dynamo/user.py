from django.utils import timezone

from .base import (
    Item,
    ItemField,
    HashKeyField,
    BOOL,
    JSON,
    NUMBER,
    DATETIME,
    STRING_SET,
)
from .base.types import DOUBLE_NEWLINE


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
    activities = ItemField(data_type=STRING_SET)
    affiliations = ItemField(data_type=JSON)
    books = ItemField(data_type=STRING_SET)
    devices = ItemField(data_type=JSON)
    friend_request_count = ItemField(data_type=NUMBER)
    has_timeline = ItemField(data_type=BOOL)
    interests = ItemField(data_type=STRING_SET)
    languages = ItemField(data_type=JSON)
    likes_count = ItemField(data_type=NUMBER)
    movies = ItemField(data_type=STRING_SET)
    music = ItemField(data_type=STRING_SET)
    political = ItemField(data_type=STRING_SET)
    profile_update_time = ItemField(data_type=DATETIME)
    quotes = ItemField(data_type=STRING_SET(DOUBLE_NEWLINE))
    relationship_status = ItemField()
    religion = ItemField()
    sports = ItemField(data_type=JSON)
    tv = ItemField(data_type=STRING_SET)
    wall_count = ItemField(data_type=NUMBER)

    @property
    def age(self):
        try:
            born = self.birthday.date()
        except AttributeError:
            # user has no birthday defined
            return None

        today = timezone.now().date()

        try:
            birthday = born.replace(year=today.year)
        except ValueError:
            # user born Feb 29
            birthday = born.replace(year=today.year, day=(born.day - 1))

        if birthday > today:
            return today.year - born.year - 1
        else:
            return today.year - born.year

    @property
    def name(self):
        return ' '.join(part for part in (self.fname, self.lname) if part)
