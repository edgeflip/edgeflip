import collections
import logging
import itertools
from unidecode import unidecode

from django.utils import timezone

from targetshare.models import dynamo


LOG = logging.getLogger(__name__)


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
        return tuple(edge.secondary.id for edge in self._edges())

    def copy(self):
        return type(self)(self)

    __copy__ = copy

    def __add__(self, other):
        """Return a new collection of these tiers with the tiers of the given collection
        added to the end.

        """
        return type(self)(itertools.chain(self, other))

    def _reranked(self, ranking):
        """Generate a stream of the collection's tiers with edges reranked according to
        the given ranking.

        """
        for tier in self:
            edge_ids = set(edge.secondary.id for edge in tier['edges'])
            reranked = []
            for edge in ranking:
                if edge.secondary.id in edge_ids:
                    reranked.append(edge)
                    edge_ids.remove(edge.secondary.id)

            if edge_ids:
                # the new ranking was missing some edges. Note it in
                # the logs, then iterate through the original order and
                # append the remaining edges to the end of the list
                LOG.warn("Edges missing (%d) from new edge rankings for user %s",
                         len(edge_ids), tier['edges'][0].primary.id)
                for edge in tier['edges']:
                    if edge.secondary.id in edge_ids:
                        reranked.append(edge)
                        edge_ids.remove(edge.secondary.id)

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


def unidecodeSafe(s):
    """util func to deal with None, numbers, and unisuck

    XXX I can probably die

    If `s` is None, returns '?'. Otherwise uses :mod:`unidecode` to produce a reasonable bytestring.

    :arg unicode s: a unicode string to convert to bytes
    :returns: a reasonable-looking ASCII bytestring
    :rtype: str
    :raises ValueError: if s is not unicode or None
    """
    if (s is None):
        return "?"
    elif not isinstance(s, unicode):
        raise TypeError("expected unicode, got %s" % type(s))
    else:
        try:
            return str(s)
        except UnicodeEncodeError:
            return unidecode(s)


# TODO: replace following with model objects (except possibly FriendInfo) #

class UserInfo(object):
    """basic facebook data from a user's profile

    some attrs may be missing

    """

    def __init__(self, uid, first_name, last_name, email, sex, birthday, city, state):
        self.id = uid
        self.fname = first_name
        self.lname = last_name
        self.email = email
        self.gender = sex
        self.birthday = birthday
        # Birthday is currently a DateTimeField in MySQL, so let's treat
        # our comparisons as such for now. Later this can be fixed, after
        # the Users table moves to Dynamo
        self.age = int(
            (timezone.now() - self.birthday).days / 365.25) if (birthday) else None
        self.city = city
        self.state = state

    def __str__(self):
        rets = [str(self.id),
                 unidecodeSafe(self.fname),
                 unidecodeSafe(self.lname),
                 self.gender,
                 str(self.age),
                 unidecodeSafe(self.city),
                 unidecodeSafe(self.state)]
        return " ".join(rets)

    @classmethod
    def from_dynamo(cls, x):
        """make a `datastructs.UserInfo` from a `dynamo` dict."""
        return cls(uid=int(x['fbid']),
                   first_name=x.get('fname'),
                   last_name=x.get('lname'),
                   email=x.get('email'),
                   sex=x.get('gender'), # XXX aaah!
                   birthday=x.get('birthday'),
                   city=x.get('city'),
                   state=x.get('state'))

    def to_dynamo(self):
        return dynamo.User({
            'fbid': self.id,
            'fname': self.fname,
            'lname': self.lname,
            'email': self.email,
            'gender': self.gender,
            'birthday': self.birthday,
            'city': self.city,
            'state': self.state,
        })


class FriendInfo(UserInfo):
    """same as a UserInfo w/ addtional fields relative to a target user

    target user = idPrimary
    """

    def __init__(self, primId, friendId, first_name, last_name, email, sex, birthday, city, state, primPhotoTags, otherPhotoTags, mutual_friend_count):
        super(FriendInfo, self).__init__(friendId, first_name, last_name, email, sex, birthday, city, state)
        self.idPrimary = primId
        self.primPhotoTags = primPhotoTags
        self.otherPhotoTags = otherPhotoTags
        self.mutuals = mutual_friend_count


class TokenInfo(object):
    """auth token for a user

    friends never have a token, just primary user

    ownerId: which user this token is for
    expires: when the token expires as datetime string
    """

    def __init__(self, tok, own, app, exp):
        self.tok = tok
        self.ownerId = own
        self.appId = app
        self.expires = exp

    def __str__(self):
        return "%s:%s %s (exp %s)" % (self.appId, self.ownerId, self.tok, self.expires.strftime("%m/%d"))

    @classmethod
    def from_dynamo(cls, x):
        """make a `datastructs.TokenInfo` from a `dynamo` dict"""
        return cls(tok=x['token'],
                   own=int(x['fbid']),
                   app=int(x['appid']),
                   exp=x['expires'])


EdgeBase = collections.namedtuple('EdgeBase',
    ('primary', 'secondary', 'incoming', 'outgoing', 'score'))


class Edge(EdgeBase):
    """Relationship between a network's primary user and a secondary user.

    Arguments:
        primary: User
        secondary: User
        incoming: IncomingEdge (primary to secondary relationship)
        outgoing: OutgoingEdge (secondary to primary relationship)
        score: proximity score (optional)

    """
    __slots__ = () # No need for object __dict__ or stored attributes

    def __new__(cls, primary, secondary, incoming, outgoing, score=None):
        return super(Edge, cls).__new__(primary, secondary, incoming, outgoing, score)

    @classmethod
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
        secondary_edges_in = {edge['fbid_source']: edge for edge in incoming_edges
                              if not require_incoming or edge['post_likes'] is not None}

        incoming_users = dynamo.User.items.batch_get(keys=[
            {'fbid': fbid} for fbid in secondary_edges_in
        ])
        secondary_users = {user['fbid']: user for user in incoming_users}

        if require_outgoing:
            # Build iterator of (secondary's ID, User, incoming edge, outgoing edge),
            # fetching outgoing edges from Dynamo.
            outgoing_edges = dynamo.OutgoingEdge.items.query(**edge_filters)
            secondary_edges_out = dynamo.IncomingEdge.items.batch_get(keys=[
                edge.get_keys() for edge in outgoing_edges
            ])
            data = (
                (
                    edge['fbid_target'],
                    secondary_users.get(edge['fbid_target']),
                    secondary_edges_in.get(edge['fbid_target']),
                    edge,
                )
                for edge in secondary_edges_out
            )
        else:
            data = (
                (
                    fbid,
                    secondary_users.get(fbid),
                    edge,
                    None,
                )
                for fbid, edge in secondary_edges_in.items()
            )

        return tuple(cls(primary, *datum[1:]) for datum in data
                     if cls._friend_edge_ok(*datum))

    @staticmethod
    def _friend_edge_ok(fbid, secondary, incoming, outgoing):
        if secondary is None:
            LOG.error("Secondary %r found in edges but not in users", fbid)
            return False

        if incoming is None:
            LOG.warn("Edge for user %r found in outgoing but not in incoming edges", fbid)
            return False

        return True

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join('{}={!r}'.format(key, value)
                      for key, value in itertools.izip(self._fields, self))
        )


class EdgeAggregator(object):
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

    @classmethod
    def ranked(cls, edges, require_incoming=True, require_outgoing=True):
        """Construct from those given a list of Edges sorted by score."""
        LOG.info("ranking %d edges", len(edges))
        edges_max = cls(edges,
                        require_incoming=require_incoming,
                        require_outgoing=require_outgoing)
        return sorted(
            (edge._replace(score=edges_max.score(edge)) for edge in edges),
            key=lambda edge: edge.score,
            reverse=True,
        )

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
                pxTotal += float(count) / countMax * weight
                weightTotal += weight
        try:
            return pxTotal / weightTotal
        except ZeroDivisionError:
            return 0


def get_ranking_best_avail(incoming_edges, all_edges, threshold=0.5):
    """Conditionally rank either only the incoming Edges or both incoming and
    outgoing Edges.

    incoming_edges: list of incoming Edges
    all_edges: list of incoming + outgoing Edges

    """
    if len(incoming_edges) * threshold > len(all_edges):
        return EdgeAggregator.ranked(incoming_edges, require_outgoing=False)
    else:
        return EdgeAggregator.ranked(all_edges, require_outgoing=True)
