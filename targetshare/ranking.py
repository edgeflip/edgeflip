import logging


LOG = logging.getLogger(__name__)


class EdgeAggregator(object):
    """scoring function

    edgesSource: list of datastructs.Edge from a primary to all friends
    aggregFunc: a function over properties of Edges (usually max)

    """
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

    def __init__(self, edgesSource, aggregFunc, requireIncoming=True, requireOutgoing=True):
        if len(edgesSource) == 0:
            return

        # these are defined even if requireIncoming is False, even though they are stored in incoming
        self.inPhotoTarget = aggregFunc(e.incoming.photos_target for e in edgesSource)
        self.inPhotoOther = aggregFunc(e.incoming.photos_other for e in edgesSource)
        self.inMutuals = aggregFunc(e.incoming.mut_friends for e in edgesSource)

        if requireIncoming:
            self.inPostLikes = aggregFunc(e.incoming.post_likes for e in edgesSource)
            self.inPostComms = aggregFunc(e.incoming.post_comms for e in edgesSource)
            self.inStatLikes = aggregFunc(e.incoming.stat_likes for e in edgesSource)
            self.inStatComms = aggregFunc(e.incoming.stat_comms for e in edgesSource)
            self.inWallPosts = aggregFunc(e.incoming.wall_posts for e in edgesSource)
            self.inWallComms = aggregFunc(e.incoming.wall_comms for e in edgesSource)
            self.inTags = aggregFunc(e.incoming.tags for e in edgesSource)

        if requireOutgoing:
            self.outPostLikes = aggregFunc(e.outgoing.post_likes for e in edgesSource)
            self.outPostComms = aggregFunc(e.outgoing.post_comms for e in edgesSource)
            self.outStatLikes = aggregFunc(e.outgoing.stat_likes for e in edgesSource)
            self.outStatComms = aggregFunc(e.outgoing.stat_comms for e in edgesSource)
            self.outWallPosts = aggregFunc(e.outgoing.wall_posts for e in edgesSource)
            self.outWallComms = aggregFunc(e.outgoing.wall_comms for e in edgesSource)
            self.outTags = aggregFunc(e.outgoing.tags for e in edgesSource)
            self.outPhotoTarget = aggregFunc(e.outgoing.photos_target for e in edgesSource)
            self.outPhotoOther = aggregFunc(e.outgoing.photos_other for e in edgesSource)
            self.outMutuals = aggregFunc(e.outgoing.mut_friends for e in edgesSource)


def prox(e, edge_max):
    """proximity - scoring function

    e: a single datastructs.Edge
    edge_max: EdgeAggregator
    rtype: score, float

    """
    countMaxWeightTups = []
    if e.incoming is not None:
        countMaxWeightTups.extend([
            # px3
            (e.incoming.mut_friends, edge_max.inMutuals, 0.5),
            (e.incoming.photos_target, edge_max.inPhotoTarget, 2.0),
            (e.incoming.photos_other, edge_max.inPhotoOther, 1.0),

            # px4
            (e.incoming.post_likes, edge_max.inPostLikes, 1.0),
            (e.incoming.post_comms, edge_max.inPostComms, 1.0),
            (e.incoming.stat_likes, edge_max.inStatLikes, 2.0),
            (e.incoming.stat_comms, edge_max.inStatComms, 1.0),
            (e.incoming.wall_posts, edge_max.inWallPosts, 1.0),        # guessed weight
            (e.incoming.wall_comms, edge_max.inWallComms, 1.0),        # guessed weight
            (e.incoming.tags, edge_max.inTags, 1.0)
        ])

    if e.outgoing is not None:
        countMaxWeightTups.extend([
            # px3
            (e.outgoing.mut_friends, edge_max.outMutuals, 0.5),
            (e.outgoing.photos_target, edge_max.outPhotoTarget, 1.0),
            (e.outgoing.photos_other, edge_max.outPhotoOther, 1.0),

            # px5
            (e.outgoing.post_likes, edge_max.outPostLikes, 2.0),
            (e.outgoing.post_comms, edge_max.outPostComms, 3.0),
            (e.outgoing.stat_likes, edge_max.outStatLikes, 2.0),
            (e.outgoing.stat_comms, edge_max.outStatComms, 16.0),
            (e.outgoing.wall_posts, edge_max.outWallPosts, 2.0),    # guessed weight
            (e.outgoing.wall_comms, edge_max.outWallComms, 3.0),    # guessed weight
            (e.outgoing.tags, edge_max.outTags, 1.0)
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


def getFriendRanking(edges, requireIncoming=True, requireOutgoing=True):
    """Construct a list of edges sorted by score, from those given."""
    LOG.info("ranking %d edges", len(edges))
    edges_max = EdgeAggregator(edges, max, requireIncoming, requireOutgoing)
    return sorted(
        (edge._replace(score=prox(edge, edges_max)) for edge in edges),
        key=lambda edge: edge.score,
        reverse=True,
    )


def getFriendRankingBestAvail(userId, edgesPart, edgesFull, threshold=0.5):
    """conditionally call getFriendRanking

    edgesPart: list of incoming Edges
    edgesFull: list of incoming + outgoing Edges
    """

    edgeCountPart = len(edgesPart)
    edgeCountFull = len(edgesFull)
    if edgeCountPart * threshold > edgeCountFull:
        return getFriendRanking(edgesPart, requireOutgoing=False)
    else:
        return getFriendRanking(edgesFull, requireOutgoing=True)
