from collections import defaultdict

from django.utils import timezone

from .base import (
    Item,
    ItemField,
    HashKeyField,
    UpsertStrategy,
    BOOL,
    JSON,
    NUMBER,
    DATETIME,
    STRING_SET,
)
from .base.types import DOUBLE_NEWLINE


class Topics(dict):

    __slots__ = ()

    @classmethod
    def classify(cls, *posts):
        """Dummy text classifier."""
        # TODO: REPLACE WITH ACTUAL CLASSIFIER
        dummy_classifications = {
            'Health:Heart Disease': 8.2,
            'Sports': 0.3,
            'Sports:Badmitton': 0.2,
        }
        return cls((post_id, dummy_classifications) for (post_id, _text) in posts)

    # Define mapping addition, whereby match weights are summed
    # (upsert must use dict.update)

    def __iadd__(self, other):
        if not isinstance(other, dict):
            raise TypeError(
                'can only concatenate Topics mapping (not "%s") to Topics'
                % other.__class__.__name__
            )

        for (post_id, classifications) in other.items():
            classifications_self = self.setdefault(post_id, {})
            for (key, value) in classifications.items():
                classifications_self[key] = classifications_self.get(key, 0) + value

        return self

    def __add__(self, other):
        new = type(self)()
        new += self
        new += other
        return new

    def aggregate(self):
        totals = defaultdict(int)
        for classifications in self.itervalues():
            for (key, value) in classifications.iteritems():
                totals[key] += value
        return totals

    def __str__(self):
        # Show aggregate weights but using dict format (not defaultdict):
        return "{}".format(dict(self.aggregate()))


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

    # Computed fields
    topics = ItemField(data_type=JSON(cls=Topics),
                       upsert_strategy=UpsertStrategy.dict_update)

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
