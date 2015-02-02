import collections
import logging

from faraday import (
    Item,
    ItemField,
    HashKeyField,
    BOOL,
    JSON,
    NUMBER,
    DATETIME,
    STRING_SET,
    types,
    utils,
)

from targetshare.utils import atan_norm

from . import PostTopics


LOG = logging.getLogger('crow')


class User(Item):

    fbid = HashKeyField(data_type=NUMBER)
    birthday = ItemField(data_type=DATETIME)
    fname = ItemField()
    lname = ItemField()
    email = ItemField()
    gender = ItemField()
    city = ItemField()
    state = ItemField()
    country = ItemField()

    # Extended fields
    activities = ItemField(data_type=STRING_SET)
    affiliations = ItemField(data_type=JSON)
    bio = ItemField()
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
    quotes = ItemField(data_type=STRING_SET(types.DOUBLE_NEWLINE))
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

        today = utils.epoch.utcnow().date()

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
        return u' '.join(part for part in (self.fname, self.lname) if part)

    @property
    def uid(self):
        return self.fbid

    @property
    def full_location(self):
        return u'{}, {} {}'.format(self.city, self.state, self.country)

    @staticmethod
    def get_topics(post_interactions, post_topics):
        """Return a User's interests scored by topic, given an iterable of the user's
        PostInteractions and a catalog of PostTopics.

        """
        scores = collections.defaultdict(int)
        for interaction in post_interactions:
            try:
                catalogued = post_topics[interaction.postid]
            except KeyError:
                topics = {}
            else:
                topics = catalogued.document

            for (topic, value) in topics.items():
                # For now, all interactions weighted the same:
                for (_interaction_type, count) in interaction.document.items():
                    scores[topic] += value * count

        # Normalize topic scores to 1:
        return {topic: atan_norm(value) for (topic, value) in scores.items()}

    @utils.cached_property
    def topics(self):
        """Aggregate topics scores of posts in which user has interacted."""
        post_interactions_set = self.postinteractions_set.all()
        (post_topics_set, _missing) = PostTopics.items.batch_get_best(
            post_interactions.postid for post_interactions in post_interactions_set
        )
        post_topics_catalog = {post_topics.postid: post_topics for post_topics in post_topics_set}
        return self.get_topics(post_interactions_set, post_topics_catalog)
