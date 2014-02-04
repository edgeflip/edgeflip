import collections
import logging
import itertools
import operator

from django.utils import timezone

from targetshare.models import dynamo
from targetshare.utils import classonlymethod


LOG = logging.getLogger(__name__)


_EdgeBase = collections.namedtuple('EdgeBase',
    ['primary', 'secondary', 'incoming', 'outgoing', 'interactions', 'score'])


class Edge(_EdgeBase):
    """Relationship between a network's primary user and a secondary user.

    Arguments:
        primary: User
        secondary: User
        incoming: IncomingEdge (primary to secondary relationship)
        outgoing: OutgoingEdge (secondary to primary relationship) (optional)
        interactions: sequence of PostInteractions (made by secondary) (optional)
        score: proximity score (optional)

    """
    __slots__ = () # No need for object __dict__ or stored attributes

    # Set outgoing, interactions and score defaults:
    def __new__(cls, primary, secondary, incoming, outgoing=None, interactions=(), score=None):
        return super(Edge, cls).__new__(cls, primary, secondary, incoming,
                                        outgoing, interactions, score)

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join('{}={!r}'.format(key, value)
                    for key, value in itertools.izip(self._fields, self))
        )


class UserNetwork(list):

    Edge = Edge

    @classonlymethod
    def get_friend_edges(cls, primary,
                         require_incoming=False,
                         require_outgoing=False,
                         max_age=None):
        newer_than_date = max_age and (timezone.now() - max_age)
        edge_filters = {'fbid_target__eq': primary['fbid']}
        if newer_than_date:
            edge_filters.update(
                index='updated',
                updated__gt=newer_than_date,
            )

        incoming_edges = dynamo.IncomingEdge.items.query(**edge_filters)
        edges_in = {edge.fbid_source: edge for edge in incoming_edges
                    if not require_incoming or edge.post_likes is not None}

        incoming_users = dynamo.User.items.batch_get(keys=[
            {'fbid': fbid} for fbid in edges_in
        ])
        secondaries = {user.fbid: user for user in incoming_users}

        if not secondaries:
            # The network is empty
            return cls()

        # Grab all PostInteractions, via PostInteractionsSet:
        post_interactions = dynamo.PostInteractions.items.batch_get_through(
            dynamo.PostInteractionsSet,
            [user.get_keys() for user in secondaries.itervalues()]
        )

        # Build hash of fbid: [PostInteractions, ...]
        interactions_key = operator.attrgetter('fbid')
        interactions_sorted = sorted(post_interactions, key=interactions_key)
        interactions_grouped = itertools.groupby(interactions_sorted, interactions_key)
        user_interactions = {fbid: set(interactions)
                             for (fbid, interactions) in interactions_grouped}

        # Build iterable of edges with secondaries, consisting of:
        # (2nd's ID, 2nd's User, incoming edge, outgoing edge, 2nd's interactions)
        if require_outgoing:
            # ...fetching outgoing edges too:
            outgoing_edges = dynamo.OutgoingEdge.incoming_edges.query(**edge_filters)
            edge_args = (
                (edge.fbid_target,
                 secondaries.get(edge.fbid_target),
                 edges_in.get(edge.fbid_target),
                 edge,
                 user_interactions.get(edge.fbid_target, set()))
                for edge in outgoing_edges)
        else:
            edge_args = (
                (fbid,
                 secondaries.get(fbid),
                 edge,
                 None,
                 user_interactions.get(fbid, set()))
                for (fbid, edge) in edges_in.items())

        return cls(
            cls.Edge(primary, secondary, incoming, outgoing, interactions)
            for (fbid, secondary, incoming, outgoing, interactions) in edge_args
            if cls._db_edge_ok(fbid, secondary, incoming, outgoing)
        )

    @staticmethod
    def _db_edge_ok(fbid, secondary, incoming, outgoing):
        if secondary is None:
            LOG.error("Secondary %r found in edges but not in users", fbid)
            return False

        if incoming is None:
            LOG.warn("Edge for user %r found in outgoing but not in incoming edges", fbid)
            return False

        return True

    __slots__ = ()

    def __init__(self, edges=()):
        super(UserNetwork, self).__init__(self._import_edges(edges))

    def _clone(self, edges=None):
        """Handle for copying over __slots__, should any exist."""
        edges = self if edges is None else edges
        return type(self)(edges)

    def __getitem__(self, key):
        result = super(UserNetwork, self).__getitem__(key)
        return self._clone(result) if isinstance(key, slice) else result

    def __getslice__(self, start, stop):
        return self.__getitem__(slice(start, stop))

    def __eq__(self, other):
        try:
            primary = other.primary
        except AttributeError:
            return False
        else:
            return primary == self.primary and super(UserNetwork, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        return self._clone(itertools.chain(self, other))

    def __mul__(self, count):
        return self._clone(itertools.chain.from_iterable(itertools.repeat(self, count)))

    __rmul__ = __mul__

    def _import_edge(self, edge):
        if self and edge.primary != self.primary:
            raise ValueError("Edge network mismatch")
        return edge

    def _import_edges(self, edges):
        for edge in edges:
            yield self._import_edge(edge)

    def append(self, edge):
        return super(UserNetwork, self).append(self._import_edge(edge))

    def extend(self, edges):
        return super(UserNetwork, self).extend(self._import_edges(edges))

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            value = self._import_edges(value)
        else:
            value = self._import_edge(value)
        return super(UserNetwork, self).__setitem__(self, key, value)

    def __setslice__(self, start, stop, sequence):
        return self.__setitem__(slice(start, stop), sequence)

    def insert(self, index, value):
        return super(UserNetwork, self).insert(index, self._import_edge(value))

    @property
    def primary(self):
        return self[0].primary

    def iter_interactions(self):
        for edge in self:
            for post_interactions in edge.interactions:
                yield post_interactions

    def precache_topics_feature(self, post_topics=None):
        """Populate secondaries' "topics" feature from the network's
        PostInteractions and PostTopics.

        User.topics is an auto-caching property, but which operates by talking to
        the database. For performance, these caches may be prepopulated from the
        in-memory UserNetwork.

        Note: If the network's PostInteractions have not themselves cached their
        field links to PostTopics, invoking this method may be database-intensive
        itself. To precache these links, an iterable of PostTopics may be specified
        (`post_topics`).

        """
        if post_topics is not None:
            # Ensure precaching of PostInteractions.post_topics
            post_topics = {pt.postid: pt for pt in post_topics}
            link = dynamo.PostInteractions.post_topics
            for post_interactions in self.iter_interactions():
                if link.cache_get(post_interactions) is None:
                    pt = post_topics.get(post_interactions.postid)
                    if pt is not None:
                        link.cache_set(post_interactions, pt)

        for edge in self:
            user = edge.secondary
            user.topics = user.get_topics(edge.interactions)

    def scored(self, require_incoming=False, require_outgoing=False):
        """Construct a new UserNetwork with scored Edges."""
        edges_max = EdgeAggregate(self,
                                  aggregator=max,
                                  require_incoming=require_incoming,
                                  require_outgoing=require_outgoing)
        return self._clone(
            edge._replace(score=edges_max.score(edge)) for edge in self
        )

    def rank(self):
        """Sort the UserNetwork by its Edges' scores."""
        self.sort(key=lambda edge: edge.score, reverse=True)

    def ranked(self, require_incoming=False, require_outgoing=False):
        """Construct a new UserNetwork, with scored Edges, ranked by these scores."""
        network = self.scored(require_incoming, require_outgoing)
        network.rank()
        return network

    def write(self):
        """Batch-write the given iterable of Edges to the database."""
        incoming_items = dynamo.IncomingEdge.items
        outgoing_items = dynamo.OutgoingEdge.items
        with incoming_items.batch_write() as incoming, outgoing_items.batch_write() as outgoing:
            for composite in self:
                for edge in (composite.incoming, composite.outgoing):
                    if edge:
                        incoming.put_item(edge)
                        outgoing.put_item(dynamo.OutgoingEdge.from_incoming(edge))

    def __repr__(self):
        return "<{}({}{})>".format(self.__class__.__name__,
                                   "{}: ".format(self.primary.fbid) if self else "",
                                   super(UserNetwork, self).__repr__())


class TieredEdges(tuple):
    """Collection of Edges ranked into tiered tuples."""
    __slots__ = () # No need for object __dict__ or stored attributes

    def __new__(cls, tiers=(), edges=(), **top_tier):
        """Instantiate a new collection from an iterable of `tiers` or by specifying the
        contents of an optional top tier (its `edges` and metadata).

        """
        tiers = () if tiers is None else tiers
        if edges or top_tier:
            top_tier['edges'] = tuple(() if edges is None else edges)
            tiers = itertools.chain([top_tier], tiers)
        return super(TieredEdges, cls).__new__(cls, tiers)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__,
                                 super(TieredEdges, self).__repr__())

    def _edges(self):
        return itertools.chain.from_iterable(tier['edges'] for tier in self)

    def __len__(self):
        return sum(1 for _edge in self._edges())

    @property
    def edges(self):
        """All edges contained in the collection, untiered."""
        return tuple(self._edges())

    @property
    def secondaries(self):
        """All edge secondaries contained in the collection."""
        return tuple(edge.secondary for edge in self._edges())

    @property
    def secondary_ids(self):
        """All edge secondaries' IDs."""
        return tuple(edge.secondary.fbid for edge in self._edges())

    def copy(self):
        return type(self)(self)

    __copy__ = copy

    def __add__(self, other):
        """Return a new collection of these tiers with the tiers of the given collection
        added to the end.

        """
        return type(self)(itertools.chain(self, other))

    def _reranked(self, ranking):
        """Generate a stream of the collection's tiers with edges reranked and
        populated from the given ranking.

        """
        for tier in self:
            edge_ids = set(edge.secondary.fbid for edge in tier['edges'])
            reranked = []
            for edge in ranking:
                if edge.secondary.fbid in edge_ids:
                    reranked.append(edge)
                    edge_ids.remove(edge.secondary.fbid)

            if edge_ids:
                # the new ranking was missing some edges. Note it in
                # the logs, then iterate through the original order and
                # append the remaining edges to the end of the list
                LOG.warn("Edges missing (%d) from new edge rankings for user %s",
                         len(edge_ids), tier['edges'][0].primary.fbid)
                for edge in tier['edges']:
                    if edge.secondary.fbid in edge_ids:
                        reranked.append(edge)
                        edge_ids.remove(edge.secondary.fbid)

            tier = tier.copy()
            tier['edges'] = reranked
            yield tier

    def reranked(self, ranking):
        """Return a new collection of these tiers, with each tier's edges reranked
        according to the given ranking.

        For instance, if the tiers were generated using px3 scores but px4 has now become
        available, we can maintain the tiers while providing a better order within them.

        """
        return type(self)(self._reranked(ranking))


class EdgeAggregate(object):
    """Edge aggregation, scoring and ranking."""

    inPhotoTarget = None
    inPhotoOther = None
    inMutuals = None

    inPostLikes = None
    inPostComms = None
    inStatLikes = None
    inStatComms = None
    inWallPosts = None
    inWallComms = None
    inTags = None

    outPostLikes = None
    outPostComms = None
    outStatLikes = None
    outStatComms = None
    outWallPosts = None
    outWallComms = None
    outTags = None
    outPhotoTarget = None
    outPhotoOther = None
    outMutuals = None

    def __init__(self, edges, aggregator=max, require_incoming=True, require_outgoing=True):
        """Apply the aggregator to the given Edges to initialize instance data.

            edges: sequence of Edges from a primary to all friends
            aggregator: a function over properties of Edges (default: max)

        """
        if len(edges) == 0:
            return

        # these are defined even if require_incoming is False, even though they are stored in incoming
        self.inPhotoTarget = aggregator(edge.incoming.photos_target for edge in edges)
        self.inPhotoOther = aggregator(edge.incoming.photos_other for edge in edges)
        self.inMutuals = aggregator(edge.incoming.mut_friends for edge in edges)

        if require_incoming:
            self.inPostLikes = aggregator(edge.incoming.post_likes for edge in edges)
            self.inPostComms = aggregator(edge.incoming.post_comms for edge in edges)
            self.inStatLikes = aggregator(edge.incoming.stat_likes for edge in edges)
            self.inStatComms = aggregator(edge.incoming.stat_comms for edge in edges)
            self.inWallPosts = aggregator(edge.incoming.wall_posts for edge in edges)
            self.inWallComms = aggregator(edge.incoming.wall_comms for edge in edges)
            self.inTags = aggregator(edge.incoming.tags for edge in edges)

        if require_outgoing:
            self.outPostLikes = aggregator(edge.outgoing.post_likes for edge in edges)
            self.outPostComms = aggregator(edge.outgoing.post_comms for edge in edges)
            self.outStatLikes = aggregator(edge.outgoing.stat_likes for edge in edges)
            self.outStatComms = aggregator(edge.outgoing.stat_comms for edge in edges)
            self.outWallPosts = aggregator(edge.outgoing.wall_posts for edge in edges)
            self.outWallComms = aggregator(edge.outgoing.wall_comms for edge in edges)
            self.outTags = aggregator(edge.outgoing.tags for edge in edges)
            self.outPhotoTarget = aggregator(edge.outgoing.photos_target for edge in edges)
            self.outPhotoOther = aggregator(edge.outgoing.photos_other for edge in edges)
            self.outMutuals = aggregator(edge.outgoing.mut_friends for edge in edges)

    def score(self, edge):
        """proximity-scoring function

        edge: a single datastructs.Edge
        rtype: score, float

        """
        countMaxWeightTups = []
        if edge.incoming is not None:
            countMaxWeightTups.extend([
                # px3
                (edge.incoming.mut_friends, self.inMutuals, 0.5),
                (edge.incoming.photos_target, self.inPhotoTarget, 2.0),
                (edge.incoming.photos_other, self.inPhotoOther, 1.0),

                # px4
                (edge.incoming.post_likes, self.inPostLikes, 1.0),
                (edge.incoming.post_comms, self.inPostComms, 1.0),
                (edge.incoming.stat_likes, self.inStatLikes, 2.0),
                (edge.incoming.stat_comms, self.inStatComms, 1.0),
                (edge.incoming.wall_posts, self.inWallPosts, 1.0),        # guessed weight
                (edge.incoming.wall_comms, self.inWallComms, 1.0),        # guessed weight
                (edge.incoming.tags, self.inTags, 1.0)
            ])

        if edge.outgoing is not None:
            countMaxWeightTups.extend([
                # px3
                (edge.outgoing.mut_friends, self.outMutuals, 0.5),
                (edge.outgoing.photos_target, self.outPhotoTarget, 1.0),
                (edge.outgoing.photos_other, self.outPhotoOther, 1.0),

                # px5
                (edge.outgoing.post_likes, self.outPostLikes, 2.0),
                (edge.outgoing.post_comms, self.outPostComms, 3.0),
                (edge.outgoing.stat_likes, self.outStatLikes, 2.0),
                (edge.outgoing.stat_comms, self.outStatComms, 16.0),
                (edge.outgoing.wall_posts, self.outWallPosts, 2.0),    # guessed weight
                (edge.outgoing.wall_comms, self.outWallComms, 3.0),    # guessed weight
                (edge.outgoing.tags, self.outTags, 1.0)
            ])

        pxTotal = 0.0
        weightTotal = 0.0
        for count, countMax, weight in countMaxWeightTups:
            if countMax:
                # counts pass thru model & become Decimal; cast to divisible types:
                pxTotal += float(count) / int(countMax) * weight
                weightTotal += weight
        try:
            return pxTotal / weightTotal
        except ZeroDivisionError:
            return 0
