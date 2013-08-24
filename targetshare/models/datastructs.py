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


class EdgeCounts(object):
    """ Stores counts of different interactions of one user on another. In all cases, counts indicate
        the actions of the source user on the target's feed.



    """
    def __init__(self, sourceId, targetId,
                 postLikes=None, postComms=None, statLikes=None, statComms=None, wallPosts=None, wallComms=None,
                 tags=None, photoTarg=None, photoOth=None, muts=None):
        self.sourceId = sourceId
        self.targetId = targetId
        self.postLikes = postLikes
        self.postComms = postComms
        self.statLikes = statLikes
        self.statComms = statComms
        self.wallPosts = wallPosts  # posts by source on target's wall
        self.wallComms = wallComms  # comments by target on those posts. These might be considered "outgoing"
                                    #   but are found in the target's stream
        self.tags = tags            # tags of the source in a target's post on the target's wall. Again,
                                    #   might be considered "outgoing" but appear in the target's stream...
        self.photoTarget = photoTarg  # count of photos owned by target in which source & target are both tagged
        self.photoOther = photoOth    # count of photos not owned by target in which source & target are both tagged
        self.mutuals = muts

    @classmethod
    def from_dynamo(cls, x):
        """make an `datastructs.EdgeCount` from a `dynamo` dict """
        return cls(
            sourceId=int(x['fbid_source']),
            targetId=int(x['fbid_target']),
            postLikes=_int_or_none(x.get('post_likes')),
            postComms=_int_or_none(x.get('post_comms')),
            statLikes=_int_or_none(x.get('stat_likes')),
            statComms=_int_or_none(x.get('stat_comms')),
            wallPosts=_int_or_none(x.get('wall_posts')),
            wallComms=_int_or_none(x.get('wall_comms')),
            tags=_int_or_none(x.get('tags')),
            photoTarg=_int_or_none(x.get('photos_target')),
            photoOth=_int_or_none(x.get('photos_other')),
            muts=_int_or_none(x.get('mut_friends'))
        )

# internal helper to convert from dynamo's decimal
_int_or_none = lambda x: int(x) if x is not None else None


class Edge(object):
    """relationship between two users

    just a container for other objects in module

    primary: UserInfo
    secondary: UserInfo
    edgeCountsIn: primary to secondary
    edgeCountsOut: secondary to primary
    """

    def __init__(self, primInfo, secInfo, edgeCountsIn, edgeCountsOut=None):
        self.primary = primInfo
        self.secondary = secInfo
        self.countsIn = edgeCountsIn
        self.countsOut = edgeCountsOut
        self.score = None

    def toDict(self):
        u = self.secondary
        d = {
            'id': u.id, 'fname': u.fname, 'lname': u.lname,
            'name': u.fname + " " + u.lname, 'gender': u.gender,
            'age': u.age, 'city': u.city, 'state': u.state,
            'score': self.score, 'desc': ''
        }
        return d
