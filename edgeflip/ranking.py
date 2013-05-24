#!/usr/bin/python
import sys

from . import database
from . import datastructs

import logging

from .settings import config

logger = logging.getLogger(__name__)


class EdgeAggregator(object):
    """scoring function

    edgesSource: list of datastructs.Edge from a primary to all friends
    aggregFunc: a function over properties of Edges (usually max)

    """

    def __init__(self, edgesSource, aggregFunc, requireIncoming=True, requireOutgoing=True):
        if (len(edgesSource) > 0):

            # these are defined even if requireIncoming is False, even though they are stored in countsIn
            self.inPhotoTarget = aggregFunc([ e.countsIn.photoTarget for e in edgesSource ])
            self.inPhotoOther = aggregFunc([ e.countsIn.photoOther for e in edgesSource ])
            self.inMutuals = aggregFunc([ e.countsIn.mutuals for e in edgesSource ])

            if (requireIncoming):
                self.inPostLikes = aggregFunc([ e.countsIn.postLikes for e in edgesSource ])
                self.inPostComms = aggregFunc([ e.countsIn.postComms for e in edgesSource ])
                self.inStatLikes = aggregFunc([ e.countsIn.statLikes for e in edgesSource ])
                self.inStatComms = aggregFunc([ e.countsIn.statComms for e in edgesSource ])
                self.inWallPosts = aggregFunc([ e.countsIn.wallPosts for e in edgesSource ])
                self.inWallComms = aggregFunc([ e.countsIn.wallComms for e in edgesSource ])
                self.inTags = aggregFunc([ e.countsIn.tags for e in edgesSource ])
            else:
                self.inPostLikes = None
                self.inPostComms = None
                self.inStatLikes = None
                self.inStatComms = None
                self.inWallPosts = None
                self.inWallComms = None
                self.inTags = None

            if (requireOutgoing):
                self.outPostLikes = aggregFunc([ e.countsOut.postLikes for e in edgesSource ])
                self.outPostComms = aggregFunc([ e.countsOut.postComms for e in edgesSource ])
                self.outStatLikes = aggregFunc([ e.countsOut.statLikes for e in edgesSource ])
                self.outStatComms = aggregFunc([ e.countsOut.statComms for e in edgesSource ])
                self.outWallPosts = aggregFunc([ e.countsOut.wallPosts for e in edgesSource ])
                self.outWallComms = aggregFunc([ e.countsOut.wallComms for e in edgesSource ])
                self.outTags = aggregFunc([ e.countsOut.tags for e in edgesSource ])
                self.outPhotoTarget = aggregFunc([ e.countsOut.photoTarget for e in edgesSource ])
                self.outPhotoOther = aggregFunc([ e.countsOut.photoOther for e in edgesSource ])
                self.outMutuals = aggregFunc([ e.countsOut.mutuals for e in edgesSource ])
            else:
                self.outPostLikes = None
                self.outPostComms = None
                self.outStatLikes = None
                self.outStatComms = None
                self.outWallPosts = None
                self.outWallComms = None
                self.outTags = None
                self.outPhotoTarget = None
                self.outPhotoOther = None
                self.outMutuals = None

def prox(e, eMax):
    """proximity - scoring function

    e: a single datastructs.Edge
    eMax: EdgeAggregator
    rtype: score, float 

    """
    countMaxWeightTups = []
    if (e.countsIn is not None):
        countMaxWeightTups.extend([
            # px3
            (e.countsIn.mutuals, eMax.inMutuals, 0.5),
            (e.countsIn.photoTarget, eMax.inPhotoTarget, 2.0),
            (e.countsIn.photoOther, eMax.inPhotoOther, 1.0),

            # px4
            (e.countsIn.postLikes, eMax.inPostLikes, 1.0),
            (e.countsIn.postComms, eMax.inPostComms, 1.0),
            (e.countsIn.statLikes, eMax.inStatLikes, 2.0),
            (e.countsIn.statComms, eMax.inStatComms, 1.0),
            (e.countsIn.wallPosts, eMax.inWallPosts, 1.0),        # guessed weight
            (e.countsIn.wallComms, eMax.inWallComms, 1.0),        # guessed weight
            (e.countsIn.tags, eMax.inTags, 1.0)
        ])

    if (e.countsOut is not None):
        countMaxWeightTups.extend([
            # px3
            (e.countsOut.mutuals, eMax.outMutuals, 0.5),
            (e.countsOut.photoTarget, eMax.outPhotoTarget, 1.0),
            (e.countsOut.photoOther, eMax.outPhotoOther, 1.0),

            # px5
            (e.countsOut.postLikes, eMax.outPostLikes, 2.0),
            (e.countsOut.postComms, eMax.outPostComms, 3.0),
            (e.countsOut.statLikes, eMax.outStatLikes, 2.0),
            (e.countsOut.statComms, eMax.outStatComms, 16.0),
            (e.countsOut.wallPosts, eMax.outWallPosts, 2.0),    # guessed weight
            (e.countsOut.wallComms, eMax.outWallComms, 3.0),    # guessed weight
            (e.countsOut.tags, eMax.outTags, 1.0)
        ])

    pxTotal = 0.0
    weightTotal = 0.0
    for count, countMax, weight in countMaxWeightTups:
        if (countMax):
            pxTotal += float(count)/countMax*weight
            weightTotal += weight
    return pxTotal / weightTotal                

def getFriendRanking(edges, requireIncoming=True, requireOutgoing=True):
    """returns sorted list of edges by score

    mutates Edges!

    edges: list of Edges

    """

    logger.info("ranking %d edges", len(edges))
    edgesMax = EdgeAggregator(edges, max, requireIncoming, requireOutgoing)
    # score each one and store it on the edge
    for e in edges:
        e.score = prox(e, edgesMax)
    return sorted(edges, key=lambda x: x.score, reverse=True)

def getFriendRankingDb(userId, requireOutgoing=True):
    """hits DB, calls getFriendRankingDb

    """

    # zzz Doesn't this function need a requireIncoming parameter to
    #     pass along to getFriendRanking?
    edgesDb = database.getFriendEdgesDb(userId, requireOutgoing)
    return getFriendRanking(edgesDb, requireOutgoing=requireOutgoing)

def getFriendRankingBestAvail(userId, edgesPart, edgesFull, threshold=0.5):
    """conditionally call getFriendRanking

    edgesPart: list of incoming Edges
    edgesFull: list of incoming + outgoing Edges
    """

    edgeCountPart = len(edgesPart)
    edgeCountFull = len(edgesFull)
    if (edgeCountPart*threshold > edgeCountFull):
        return getFriendRanking(edgesPart, requireOutgoing=False)
    else:
        return getFriendRanking(edgesFull, requireOutgoing=True)

def getFriendRankingBestAvailDb(userId, threshold=0.5):
    """hit DB & call getFriendRankingBestAvail

    """
    edgesPart = database.getFriendEdgesDb(userId, requireOutgoing=False)
    edgesFull = database.getFriendEdgesDb(userId, requireOutgoing=True)
    return getFriendRankingBestAvail(userId, edgesPart, edgesFull, threshold)
