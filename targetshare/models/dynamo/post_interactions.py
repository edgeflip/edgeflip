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

    post_topics = ItemLinkField('PostTopics', db_key=postid)
    user = ItemLinkField('User', db_key=fbid)
