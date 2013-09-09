from boto.dynamodb2 import fields

from .base import Item, ItemField, HashKeyField, RangeKeyField, NUMBER


class IncomingEdge(Item):

    fbid_target = HashKeyField(data_type=NUMBER)
    fbid_source = RangeKeyField(data_type=NUMBER)
    post_likes = ItemField()
    post_comms = ItemField()
    stat_likes = ItemField()
    stat_comms = ItemField()
    wall_posts = ItemField()
    wall_comms = ItemField()
    tags = ItemField()
    photos_target = ItemField()
    photos_other = ItemField()
    mut_friends = ItemField()

    class Meta(object):
        table_name = 'edges_incoming'
        indexes = (
            fields.IncludeIndex('updated',
                parts=[fields.HashKey('fbid_target', data_type=NUMBER),
                       fields.RangeKey('updated', data_type=NUMBER)],
                includes=['fbid_target', 'fbid_source']),
        )


class OutgoingEdge(Item):

    fbid_source = HashKeyField(data_type=NUMBER)
    fbid_target = RangeKeyField(data_type=NUMBER)

    class Meta(object):
        table_name = 'edges_outgoing'
        indexes = (
            fields.IncludeIndex('updated',
                parts=[fields.HashKey('fbid_source', data_type=NUMBER),
                       fields.RangeKey('updated', data_type=NUMBER)],
                includes=['fbid_target', 'fbid_source']),
        )
