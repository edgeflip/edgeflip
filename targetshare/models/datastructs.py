import abc
import collections
import logging
import itertools
import operator

from django.conf import settings
from django.utils import timezone

from core.utils import datastruct, names

from targetshare.models import dynamo
from targetshare.utils import classonlymethod


LOG = logging.getLogger(__name__)


# Token class for newly-received tokens, before extension and db-persistence:
ShortToken = collections.namedtuple('ShortToken', ('fbid', 'appid', 'token', 'api'))


# API 2.2 datastructs #

# Abstract models #

class Friend(datastruct.DataStruct):
    """Abstract model for all representations of users of Facebook."""

    @abc.abstractproperty
    def fbid(self):
        """The persistent user ID returned by Facebook.

        When specified, this is generally a Facebook App-scoped ID.

        Alternatively, this may be None; however, it is still given, for
        compatibility with (back-end) code wanting only true Facebook IDs.

        """
        raise NotImplementedError

    @abc.abstractproperty
    def name(self):
        """The full user name."""
        raise NotImplementedError

    @abc.abstractproperty
    def uid(self):
        """Any unique user ID returned by Facebook.

        This may be a persistent or a temporary ID. It is required for
        compatibility with (front-end) code handling both persistent users and
        transient taggable friends.

        """
        raise NotImplementedError


class Taggable(datastruct.DataStruct):
    """Abstract (mix-in) model for Facebook friends who are available to a user
    for tagging in a post.

    """
    @abc.abstractproperty
    def id(self):
        """The temporary ID returned by Facebook for use in the tag."""
        raise NotImplementedError

    @abc.abstractproperty
    def picture(self):
        """URL to a picture of the taggable friend."""
        raise NotImplementedError

    @property
    def uid(self):
        return self.id


# Concrete models #

class User(Friend):
    """Model of a Facebook user for whom we've received a persistent ID, and
    about whom we may have additional personal information.

    """
    fbid = datastruct.IntegerField()
    fname = datastruct.CharField()
    lname = datastruct.CharField()
    name = datastruct.CharField()
    gender = datastruct.CharField()
    email = datastruct.CharField(null=True)
    city = datastruct.CharField(null=True)
    state = datastruct.CharField(null=True)
    birthday = datastruct.DateField(null=True)

    def __init__(self, *args, **kws):
        super(User, self).__init__(*args, **kws)
        # May receive either full name or split-out fname and lname:
        try:
            self.name = u' '.join(part for part in (self.fname, self.lname) if part)
        except AttributeError:
            try:
                (self.fname, self.lname) = names.parse_names(self.name)
            except AttributeError:
                raise TypeError("Either 'fname' and 'lname' or 'name' required")

    @property
    def uid(self):
        return self.fbid


class TaggableUser(Taggable, User):
    """A User for whom we've also received a tagging ID and picture URL."""

    id = datastruct.CharField()
    picture = datastruct.CharField()

    @classonlymethod
    def combine(cls, user, taggable):
        """Construct a new TaggableUser by combining a given User and a given
        TaggableFriend.

        """
        if user.name != taggable.name:
            raise ValueError("{!r} != {!r}".format(user.name, taggable.name))
        data = dict(user.__dict__, id=taggable.id, picture=taggable.picture)
        return cls(**data)


class TaggableFriend(Taggable, Friend):
    """Model of a Facebook user for whom we've only received tagging information."""

    id = datastruct.CharField()
    name = datastruct.CharField()
    picture = datastruct.CharField()
    _names_ = datastruct.InternalField() # cache for parsed-out names

    fbid = None # no persistent ID

    # Parse combined "name" field into first and last on a need-to-know basis #

    @property
    def _names(self):
        try:
            return self._names_
        except AttributeError:
            self._names_ = names.parse_names(self.name)
            return self._names_

    @property
    def fname(self):
        return self._names[0]

    @property
    def lname(self):
        return self._names[1]


class DirectedEdge(datastruct.DataStruct):

    INTERACTIONS = frozenset([
        'photo_tags',
        'photo_likes',
        'photo_comms',
        'photos_target',
        'video_tags',
        'video_likes',
        'video_comms',
        'videos_target',
        'photo_upload_tags',
        'photo_upload_likes',
        'photo_upload_comms',
        'video_upload_tags',
        'video_upload_likes',
        'video_upload_comms',
        'stat_tags',
        'stat_likes',
        'stat_comms',
        'link_tags',
        'link_likes',
        'link_comms',
        'place_tags',
    ])

    target = datastruct.ReferenceField(Friend)
    source = datastruct.ReferenceField(Friend)
    score = datastruct.FloatField()

    # Magically set IntegerFields for each interaction type:
    locals().update(
        (interaction, datastruct.IntegerField(default=0))
        for interaction in INTERACTIONS
    )


class IncomingEdge(DirectedEdge):

    @property
    def secondary(self):
        return self.source

    # Quick-and-dirty compatibility with v1.0 interface #

    def get_rank_score(self, rank):
        if rank is None:
            return self.score
        raise NotImplementedError("{} does not support ranked proximity scores"
                                  .format(self.__class__.__name__))

    def get_score(self):
        return (None, self.score)


_CONFIGURED_PROXIMITY = getattr(settings, 'PROXIMITY', None) or {}


class DirectedEdgeAggregate(object):

    weights = {interaction: _CONFIGURED_PROXIMITY.get(interaction, 1)
               for interaction in DirectedEdge.INTERACTIONS}

    def __init__(self, network, aggregator=max):
        for interaction in self.weights:
            if network:
                population_score = aggregator(getattr(edge, interaction) for edge in network)
            else:
                population_score = 0
            setattr(self, interaction, population_score)

    def score(self, edge):
        """proximity-scoring function

        edge: a single datastructs.DirectedEdge

        """
        score_total = weight_total = 0
        for (interaction, weight) in self.weights.iteritems():
            population_score = getattr(self, interaction)
            if population_score:
                edge_score = getattr(edge, interaction)
                score_total += float(edge_score) / population_score * weight
                weight_total += weight

        try:
            return score_total / weight_total
        except ZeroDivisionError:
            return 0

    def score_all(self, network):
        for edge in network:
            edge.score = self.score(edge)


class DirectedEdges(list):

    Aggregate = DirectedEdgeAggregate
    Edge = DirectedEdge

    def __init__(self, user, edges=()):
        self.user = user
        super(DirectedEdges, self).__init__(edges)

    def __repr__(self):
        return "{}({}, {})".format(
            self.__class__.__name__,
            self.user,
            super(DirectedEdges, self).__repr__(),
        )

    def _clone(self, edges=None):
        """Handle for copying over attributes."""
        return type(self)(self.user, (self if edges is None else edges))

    def __getitem__(self, key):
        result = super(DirectedEdges, self).__getitem__(key)
        return self._clone(result) if isinstance(key, slice) else result

    def __getslice__(self, start, stop):
        return self.__getitem__(slice(start, stop))

    def __eq__(self, other):
        try:
            user = other.user
        except AttributeError:
            return False
        else:
            return user == self.user and super(DirectedEdges, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        return self._clone(itertools.chain(self, other))

    def __mul__(self, count):
        return self._clone(itertools.chain.from_iterable(itertools.repeat(self, count)))

    __rmul__ = __mul__

    def score(self):
        """Calculate normalized proximity scores for each edge in the network
        and set their `score` attribute.

        This operation is in-place.

        """
        self.Aggregate(self).score_all(self)

    def rank(self):
        """Sort the network edges, in-place, by their `score`."""
        self.sort(key=lambda edge: edge.score, reverse=True)

    def score_rank(self):
        """Score the network edges, and rank them, in-place."""
        self.score()
        self.rank()


class IncomingEdges(DirectedEdges):

    Edge = IncomingEdge

    def merged(self, *fills):
        """Return a new, ostensibly-extended network, filled in by any number
        of iterables of TaggableFriends, removing duplicates between the sets
        according to Friends' names, and replacing edges of Users with new
        edges of TaggableUsers.

        If this method fails to completely match any set of Friends under their
        shared name, only edges wrapping TaggableFriends are returned for that
        name.

        This method assumes that "fill" Friends are unique, (and that their IDs
        are unavailable or incompatible for comparison with existing edge Friends).

        `merged` does not maintain any pre-existing edge ordering.

        """
        return self._clone(self._itermerged(*fills))

    def _itermerged(self, *fills):
        lookup = collections.defaultdict(list)
        for users in fills:
            for user in users:
                lookup[user.name].append(user)

        nomatch = multimatch = 0
        edgekey = operator.attrgetter('source.name')
        for (name, edges_iter) in itertools.groupby(sorted(self, key=edgekey), edgekey):
            edges = tuple(edges_iter)
            edge_count = len(edges)
            matches = lookup[name]
            match_count = len(matches)

            # Conservative: if we're unsure at all, we fall back entirely
            # on the default list(s).
            if match_count == edge_count == 1:
                # Exact match.
                del lookup[name]
                ((edge,), (taggable_friend,)) = (edges, matches)
                yield edge.clone(source=TaggableUser.combine(edge.source, taggable_friend))
            elif match_count >= edge_count:
                # Either:
                # a) All "fill" users are accounted for in "head"; however, we
                # can't differentiate between them for the purpose of extending
                # individual users with their tagging information.
                # or:
                # b) There are "fill" users unaccounted for in "head";
                # rather than risk duplicates, fall back entirely to "fills".
                multimatch += match_count - edge_count
                LOG.debug("Multiple friend matches in name-merge (%r): %r", self.user.fbid, name)
            elif match_count < edge_count:
                # There are "head" users unaccounted for in "fills".
                # Some of these might be BAD.
                nomatch += edge_count - match_count
                LOG.debug("Unmatched friends in name-merge (%r): %r", self.user.fbid, name)

        fillcount = 0
        fillusers = itertools.chain.from_iterable(lookup.itervalues())
        for (fillcount, user) in enumerate(fillusers, 1):
            yield self.Edge(target=self.user, source=user)

        if nomatch:
            LOG.debug("No matching friends in name-merge (%r): (%r)", self.user.fbid, nomatch)
        if multimatch:
            LOG.debug("Multiple friend matches in name-merge (%r): (%r)", self.user.fbid, multimatch)
        if fillcount:
            LOG.debug("Filled in %r users via name-merge (%r)", fillcount, self.user.fbid)


# API 1.0 datastructs #

_EdgeSpec = collections.namedtuple('Edge',
    ('primary', 'secondary', 'incoming', 'outgoing', 'interactions',
     'px3_score', 'px4_score', 'px_score'))


class Edge(_EdgeSpec):
    """Relationship between a network's primary user and a secondary user.

    Arguments:
        primary: User
        secondary: User
        incoming: IncomingEdge (primary to secondary relationship)
        outgoing: OutgoingEdge (secondary to primary relationship) (optional)
        interactions: sequence of PostInteractions (made by secondary) (optional)
        px3_score: proximity "rank 3" score (optional, see below)
        px4_score: proximity "rank 4" score (optional, see below)
        px_score: unranked proximity score (optional, see below)

    An Edge may be defined with a `px_score`, or a `px3_score` and `px4_score`; but,
    `px_score` is not compatible with `px*_score` values. The property `score`
    returns either `px_score`, `px4_score` or `px3_score`, if defined, (in that order).

    """
    __slots__ = () # No need for object __dict__ or stored attributes

    # Set outgoing, interactions and score defaults:
    def __new__(cls, primary, secondary, incoming, outgoing=None,
                interactions=(), px3_score=None, px4_score=None, px_score=None):
        if px_score is not None and not (px3_score is None and px4_score is None):
            raise TypeError("Unranked score incompatible with ranked")
        return super(Edge, cls).__new__(cls, primary, secondary, incoming,
                                        outgoing, interactions, px3_score, px4_score, px_score)

    def get_rank_score(self, rank):
        if rank is None:
            return self.px_score
        return getattr(self, 'px{}_score'.format(rank))

    def get_score(self):
        if self.px_score is None:
            if self.px4_score is None:
                if self.px3_score is None:
                    raise LookupError("no score")
                return (3, self.px3_score)
            else:
                return (4, self.px4_score)
        else:
            return (None, self.px_score)

    @property
    def score(self):
        try:
            (_rank, score) = self.get_score()
        except LookupError:
            return None
        else:
            return score


class UserNetwork(list):

    Edge = Edge

    @classonlymethod
    def get_friend_edges(cls, primary,
                         require_incoming=False,
                         require_outgoing=False,
                         max_age=None):
        if max_age:
            updated_filters = {
                'index': 'updated',
                'updated__gt': (timezone.now() - max_age),
            }
        else:
            updated_filters = {}

        incoming_filters = updated_filters.copy()
        if incoming_filters:
            # (Until we project all attributes into the index), we have to make
            # an additional request to the table for non-index keys, or ask DDB
            # to do this for us (via `attributes`):
            incoming_filters['attributes'] = dynamo.IncomingEdge._meta.keys.keys()
        incoming_edges = primary.incomingedges.query(**incoming_filters)
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
            outgoing_edges = dynamo.OutgoingEdge.incoming_edges.query(
                fbid_source__eq=primary.fbid,
                **updated_filters
            )
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

    def precache_topics_feature(self, post_topics):
        """Populate secondaries' "topics" feature from the network's
        set of PostInteractions and the given set of PostTopics.

        User.topics is an auto-caching property, but which self-populates by talking to
        the database. For performance, these caches may be prepopulated from the
        in-memory UserNetwork.

        """
        topics_catalog = {pt.postid: pt for pt in post_topics}
        for edge in self:
            user = edge.secondary
            user.topics = user.get_topics(edge.interactions, topics_catalog)

    def scored(self, require_incoming=False, require_outgoing=False):
        """Construct a new UserNetwork with scored Edges."""
        edges_max = EdgeAggregate(self,
                                  aggregator=max,
                                  require_incoming=require_incoming,
                                  require_outgoing=require_outgoing)
        if require_incoming:
            mapper = lambda edge: edge._replace(px4_score=edges_max.score(edge))
        else:
            mapper = lambda edge: edge._replace(px3_score=edges_max.score(edge))

        return self._clone(mapper(edge) for edge in self)

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

    def iteredges(self):
        return itertools.chain.from_iterable(tier['edges'] for tier in self)

    def __len__(self):
        return sum(1 for _edge in self.iteredges())

    @property
    def edges(self):
        """All edges contained in the collection, untiered."""
        return tuple(self.iteredges())

    @property
    def secondaries(self):
        """All edge secondaries contained in the collection."""
        return tuple(edge.secondary for edge in self.iteredges())

    @property
    def secondary_ids(self):
        """All edge secondaries' IDs."""
        return tuple(edge.secondary.fbid for edge in self.iteredges())

    def copy(self):
        return type(self)(self)

    __copy__ = copy

    def __add__(self, other):
        """Return a new collection of these tiers with the tiers of the given collection
        added to the end.

        """
        return type(self)(itertools.chain(self, other))

    def _reranked(self, ranking, oldrank):
        """Generate a stream of the collection's tiers with edges repopulated
        from the given ranking.

        The scores of the old ranking are preserved on the new edges.

        """
        score_name = 'px{}_score'.format(oldrank)

        for tier in self:
            old_scores = {edge.secondary.fbid: getattr(edge, score_name) for edge in tier['edges']}

            reranked = []
            for edge in ranking:
                try:
                    old_score = old_scores.pop(edge.secondary.fbid)
                except KeyError:
                    pass
                else:
                    reranked.append(edge._replace(**{score_name: old_score}))

            if old_scores:
                # The new ranking was missing some edges.
                # Note it in the logs, then iterate through the original order
                # and append the remaining edges to the end of the list:
                LOG.warn("Edges missing (%d) from new edge rankings for user %s",
                         len(old_scores), tier['edges'][0].primary.fbid)
                for edge in tier['edges']:
                    try:
                        old_score = old_scores.pop(edge.secondary.fbid)
                    except KeyError:
                        pass
                    else:
                        reranked.append(edge._replace(**{score_name: old_score}))

            yield dict(tier, edges=reranked)

    def reranked(self, ranking, oldrank=3):
        """Return a copy of the sequence of tiered edges, with each tier's edges reranked
        according to the given ranking.

        For instance, if the tiers were generated using px3 scores but px4 has now become
        available, we can maintain the tiers while providing a better order within them:

            filtered_results = filtered_results.reranked(px4_ranked, 3)

        """
        return type(self)(self._reranked(ranking, oldrank))

    def _rescored(self, edges, rank):
        score_name = 'px{}_score'.format(rank)
        edge_scores = {edge.secondary.fbid: getattr(edge, score_name) for edge in edges}
        for tier in self:
            rescored_edges = []
            for edge in tier['edges']:
                score = edge_scores.get(edge.secondary.fbid, getattr(edge, score_name))
                rescored_edges.append(
                    edge._replace(**{score_name: score})
                )
            yield dict(tier, edges=rescored_edges)

    def rescored(self, edges, rank):
        """Return a copy of the tiered edges, writing to the edges the rank-
        specific scores of the given iterable of edges.

        """
        return type(self)(self._rescored(edges, rank))


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
