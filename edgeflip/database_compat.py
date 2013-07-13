"""Compatability layer for `edgeflip.database`


This module imports _everything_ from `edgeflip.database`, and then overrides
some functions with versions backed by `edgeflip.dynamo`. See their
respective documentations.
"""
# slurp database's namespace before other imports, so we can overwrite
from .database import *

import logging
import threading
import datetime
import types

from . import dynamo
from . import datastructs

logger = logging.getLogger(__name__)

def updateUsersDb(users):
    """update users table

    :arg users: a list of `datastruct.UserInfo`
    """
    # XXX it'd be nice to use boto's batch_write here, but it doesn't support partial updates
    for u in users:
        save_user(fbid=u.id, fname=u.fname, lname=u.lname, email=u.email, gender=u.gender, birthday=u.birthday, city=u.city, state=u.state)

def getUserDb(userId, freshnessDays=36525, freshnessIncludeEdge=False): # 100 years!
    """
    :rtype: datastructs.UserInfo

    freshness - how recent does data need to be? returns None if not fresh enough
    """
    if freshnessIncludeEdge:
        raise NotImplementedError("freshnessIncludeEdge must be False!")

    freshnessDate = datetime.datetime.utcnow() - datetime.timedelta(days=freshnessDays)
    logger.debug("getting user %s, freshness date is %s (GMT)" % (userId, freshnessDate.strftime("%Y-%m-%d %H:%M:%S")))

    user = dynamo.fetch_user(userId)

    if user is None or user.updated <= freshnessDate:
        return None
    else:
        logger.debug("getting user %s, update date is %s (GMT)" % (userId, user.updated.strftime("%Y-%m-%d %H:%M:%S")))
        return user

def updateTokensDb(token):
    """update tokens table

    :arg token: a `datastruct.TokenInfo`
    """

    save_token(token.ownerId, token.appId, token.tok, token.expires)

def getUserTokenDb(userId, appId):
    """grab the "best" token from the tokens table

    :rtype: datastructs.TokenInfo
    """
    return dynamo.fetch_token(userId, appId)

def updateFriendEdgesDb(edges):
    """update edges table

    :arg edges: a list of `datastruct.Edge`
    """
    # pick out all the non-None EdgeCounts from all the edges
    counts = (c for e in edges for c in (e.countsIn, e.countsOut) if c is not None)

    for c in counts:
        dynamo.save_edge(
            fbid_source=c.sourceId,
            fbid_target=c.targetId,
            post_likes=c.postLikes,
            post_comms=c.postComms,
            stat_likes=c.statLikes,
            stat_comms=c.statComms,
            wall_posts=c.wallPosts,
            wall_comms=c.wallComms,
            tags=c.tags,
            photos_target=c.photoTarget,
            photos_other=c.photoOther,
            mut_friends=c.mutuals)

def getFriendEdgesDb(primId, requireOutgoing=False, maxAge=None):
    """return list of datastructs.Edge objects for primaryId user

    """
    # xxx with support from dynamo.fetch_* returning iterators instead of
    # lists, this could all be made to stream from Dynoamo in parallel (may
    # require threads)
    assert isinstance(maxAge, (datetime.timedelta, types.NoneType))
    newer_than_date = datetime.datetime.now() - maxAge if maxAge is not None else None

    primary = getUserDb(primId)

    # build dict of secondary id -> EdgeCounts
    # XXX this is the ugliest variable name I have ever written in my life.
    secondary_EdgeCounts_in = {e.targetId : e for e in
                               dynamo.fetch_incoming_edges(primId, newer_than_date)}



    # build dict of secondary id -> UserInfo
    secondary_UserInfo = {u.id : u for u in
                          dynamo.fetch_many_users([e.targetId for e in incoming_edge_counts])}

    # early return if we don't need outgoing
    if not requireOutgoing:
        return [datastructs.Edge(primary, secondary_UserInfo[fbid], ec, None)
                for fbid, ec in secondary_EdgeCounts_in.iteritems()]

    # build iterator of (secondary's UserInfo, incoming edge, outgoing edge),
    # fetching from outgoings from Dynamo. Then turn those into Edge objects,
    # while dropping outgoings that don't have a corresponding incoming for
    # whatever reason.
    args = ((primary,
             secondary_UserInfo[ec.targetId],
             secondary_EdgeCounts_in.get(ec.targetId),
             ec)
            for ec in dynamo.fetch_outgoing_edges(primId, newer_than_date))

    return [datastructs.Edge(*a) for a in args if a[2] is not None]



# helper function that may get run in a background thread
def _updateDb(user, token, edges):
    """takes datastructs.* and writes to database
    """
    tim = datastructs.Timer()

    # update token for primary
    updateTokensDb(user, token)
    updateUsersDb([user])
    updateUsersDb([e.secondary for e in edges])
    updateFriendEdgesDb(edges)

    logger.debug("_updateDB() thread %d updated %d friends and edges for user %d (took %s)" %
                    (threading.current_thread().ident, len(edges), user.id, tim.elapsedPr()))


def updateDb(user, token, edges, background=False):
    """calls _updateDb maybe in thread"""

    if background:
        t = threading.Thread(target=_updateDb, args=(user, token, edges))
        t.daemon = False
        t.start()
        logger.debug("updateDb() spawning background thread %d for user %d", t.ident, user.id)
    else:
        logger.debug("updateDb() foreground thread %d for user %d", threading.current_thread().ident, user.id)
        _updateDb(user, token, edges)
