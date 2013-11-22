from .base import Item, ItemField, HashKeyField, RangeKeyField, NUMBER


class FeedBucketMap(Item):

    fbid_source = HashKeyField(data_type=NUMBER)
    fbid_target = RangeKeyField(data_type=NUMBER)
    bucket = ItemField()
    token = ItemField()
