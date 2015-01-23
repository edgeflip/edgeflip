from faraday import (
    Item,
    ItemField,
    ItemLinkField,
    SingleItemLinkField,
    HashKeyField,
    RangeKeyField,
    UpsertStrategy,
    NUMBER,
    STRING,
    STRING_SET,
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

    link_comms = ItemField(data_type=NUMBER)
    link_likes = ItemField(data_type=NUMBER)
    link_tags = ItemField(data_type=NUMBER)
    photo_comms = ItemField(data_type=NUMBER)
    photo_likes = ItemField(data_type=NUMBER)
    photo_tags = ItemField(data_type=NUMBER)
    photo_upload_comms = ItemField(data_type=NUMBER)
    photo_upload_likes = ItemField(data_type=NUMBER)
    photo_upload_tags = ItemField(data_type=NUMBER)
    place_tags = ItemField(data_type=NUMBER)
    stat_tags = ItemField(data_type=NUMBER)
    video_comms = ItemField(data_type=NUMBER)
    video_likes = ItemField(data_type=NUMBER)
    video_tags = ItemField(data_type=NUMBER)
    video_upload_comms = ItemField(data_type=NUMBER)
    video_upload_likes = ItemField(data_type=NUMBER)
    video_upload_tags = ItemField(data_type=NUMBER)
    videos_target = ItemField(data_type=NUMBER)

    user = ItemLinkField('User', db_key=fbid)


class PostInteractionsSet(Item):
    """Join of PostInteractions facilitating queries across Users."""
    fbid = HashKeyField(data_type=NUMBER)
    postids = ItemField(data_type=STRING_SET,
                        upsert_strategy=UpsertStrategy.update)

    user = SingleItemLinkField('User', db_key=fbid, linked_name=None)
