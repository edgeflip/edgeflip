from functools import wraps

from boto.dynamodb2 import fields

from targetshare.utils import LazyList

from .base import Item, ItemField, ItemManager, HashKeyField, RangeKeyField, NUMBER


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


class UnifiedEdgeManager(ItemManager):

    @staticmethod
    def get_data_manager():
        return IncomingEdge.items

    def _make_unified_method(method_name):
        @wraps(getattr(ItemManager, method_name), ('__name__', '__doc__'))
        def wrapped(self, *args, **kws):
            inherited_method = getattr(super(UnifiedEdgeManager, self), method_name)
            outgoing_edges = inherited_method(*args, **kws)
            # keys must be a list, but don't evaluate until caller initiates:
            keys = LazyList(outgoing_edge.get_keys() for outgoing_edge in outgoing_edges)
            return self.get_data_manager().batch_get(keys=keys)
        return wrapped

    # Populate ResultsSet methods with _make_unified_method:
    for method_name in ('batch_get', 'query', 'scan'):
        locals()[method_name] = _make_unified_method(method_name)
    del method_name

    _make_unified_method = staticmethod(_make_unified_method)

    @wraps(ItemManager.get_item, ('__name__', '__doc__'))
    def get_item(self, *args, **kws):
        item = super(UnifiedEdgeManager, self).get_item(*args, **kws)
        return self.get_data_manager().get_item(**item.get_keys())


class OutgoingEdge(Item):

    fbid_source = HashKeyField(data_type=NUMBER)
    fbid_target = RangeKeyField(data_type=NUMBER)

    incoming_edges = UnifiedEdgeManager()

    class Meta(object):
        table_name = 'edges_outgoing'
        indexes = (
            fields.IncludeIndex('updated',
                parts=[fields.HashKey('fbid_source', data_type=NUMBER),
                       fields.RangeKey('updated', data_type=NUMBER)],
                includes=['fbid_target', 'fbid_source']),
        )

    @classmethod
    def from_incoming(cls, incoming):
        return cls(fbid_source=incoming['fbid_source'],
                   fbid_target=incoming['fbid_target'])
