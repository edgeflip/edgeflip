from functools import wraps

from boto.dynamodb2 import fields

from targetshare.utils import LazyList

from .base import (
    Item,
    ItemField,
    ItemLinkField,
    ItemManager,
    HashKeyField,
    RangeKeyField,
    NUMBER,
)


class IncomingEdge(Item):

    fbid_target = HashKeyField(data_type=NUMBER)
    fbid_source = RangeKeyField(data_type=NUMBER)
    post_likes = ItemField(data_type=NUMBER)
    post_comms = ItemField(data_type=NUMBER)
    stat_likes = ItemField(data_type=NUMBER)
    stat_comms = ItemField(data_type=NUMBER)
    wall_posts = ItemField(data_type=NUMBER)
    wall_comms = ItemField(data_type=NUMBER)
    tags = ItemField(data_type=NUMBER)
    photos_target = ItemField(data_type=NUMBER)
    photos_other = ItemField(data_type=NUMBER)
    mut_friends = ItemField(data_type=NUMBER)

    primary = ItemLinkField('User', db_key=fbid_target)
    secondary = ItemLinkField('User', db_key=fbid_source, linked_name=None)

    class Meta(object):
        table_name = 'edges_incoming'
        indexes = (
            fields.IncludeIndex('updated',
                parts=[fields.HashKey('fbid_target', data_type=NUMBER),
                       fields.RangeKey('updated', data_type=NUMBER)],
                includes=['fbid_target', 'fbid_source']),
        )


class UnifiedEdgeManager(ItemManager):
    """ItemManager by which fully-defined edges (IncomingEdges) may be retrieved
    through the OutgoingEdge table (by fbid_source,fbid_target).

    """
    @staticmethod
    def get_data_manager():
        """Return the ItemManager by which IncomingEdges are queried."""
        return IncomingEdge.items

    def _make_unified_method(method_name):
        """For the given manager method, (specified by name), manufacture a unified
        query method, which will query the IncomingEdge/"data" manager for the items
        referred to by the result of a given OutgoingEdge query.

        """
        @wraps(getattr(ItemManager, method_name), ('__name__', '__doc__'))
        def wrapped(self, *args, **kws):
            inherited_method = getattr(super(UnifiedEdgeManager, self), method_name)
            result = inherited_method(*args, **kws)
            try:
                keys = result.get_keys()
            except AttributeError:
                # keys must be a list, but don't evaluate until caller initiates:
                keys = LazyList(outgoing_edge.get_keys() for outgoing_edge in result)
                return self.get_data_manager().batch_get(keys=keys)
            else:
                return self.get_data_manager().get_item(**keys)
        return wrapped

    # Populate querying methods with _make_unified_method:
    for method_name in ('get_item', 'batch_get', 'query', 'scan'):
        locals()[method_name] = _make_unified_method(method_name)
    del method_name # Clean up

    _make_unified_method = staticmethod(_make_unified_method)


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
