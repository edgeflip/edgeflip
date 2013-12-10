from .base import (
    Item,
    ItemField,
    ItemLinkField,
    HashKeyField,
    RangeKeyField,
    NUMBER,
    STRING,
)


class PostInteractions(Item):

    fbid = HashKeyField(data_type=NUMBER)
    postid = RangeKeyField(data_type=STRING)
    post_likes = ItemField(data_type=NUMBER)
    post_comms = ItemField(data_type=NUMBER)
    stat_likes = ItemField(data_type=NUMBER)
    stat_comms = ItemField(data_type=NUMBER)
    wall_posts = ItemField(data_type=NUMBER)
    wall_comms = ItemField(data_type=NUMBER)
    tags = ItemField(data_type=NUMBER)

    user = ItemLinkField('User', db_key=fbid)

    @property
    def counts(self):
        return {key: value for (key, value) in self.items()
                if key not in ('fbid', 'postid')}
