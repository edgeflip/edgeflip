import logging
import datetime
import types

from django.db import connection
from django.utils import timezone

from .models import dynamo
from .models import datastructs


logger = logging.getLogger(__name__)


def getConn():
    """return a connection for this thread."""
    return connection


def getUserDb(userId, freshnessDays=36525, freshnessIncludeEdge=False): # 100 years!
    """
    :rtype: datastructs.UserInfo

    freshness - how recent does data need to be? returns None if not fresh enough
    """
    if freshnessIncludeEdge:
        raise NotImplementedError("freshnessIncludeEdge must be False!")

    freshnessDate = timezone.now() - datetime.timedelta(days=freshnessDays)
    logger.debug("getting user %s, freshness date is %s (GMT)" % (userId, freshnessDate.strftime("%Y-%m-%d %H:%M:%S")))

    user = dynamo.fetch_user(userId)

    if user is None:
        logger.debug("user %s not found", userId)
        return None
    elif user['updated'] <= freshnessDate:
        logger.debug("user %s too old, dropped", userId)
        return None
    else:
        logger.debug("got user %s, updated at %s (GMT)" % (userId, user['updated'].strftime("%Y-%m-%d %H:%M:%S")))
        return datastructs.UserInfo.from_dynamo(user)


def getUserTokenDb(userId, appId):
    """grab the "best" token from the tokens table

    :rtype: datastructs.TokenInfo
    """
    return datastructs.TokenInfo.from_dynamo(dynamo.fetch_token(userId, appId))


def getFriendEdgesDb(primId, requireIncoming=False, requireOutgoing=False, maxAge=None):
    """Return list of datastructs.Edge objects for primaryId user."""
    # xxx with support from dynamo.fetch_* returning iterators instead of
    # lists, this could all be made to stream from Dynoamo in parallel (may
    # require threads)
    assert isinstance(maxAge, (datetime.timedelta, types.NoneType))
    newer_than_date = datetime.datetime.now() - maxAge if maxAge is not None else None

    primary = getUserDb(primId)

    # dict of secondary id -> EdgeCounts:
    if requireIncoming:
        secondary_EdgeCounts_in = {
            edge['fbid_source']: datastructs.EdgeCounts.from_dynamo(edge)
            for edge in dynamo.fetch_incoming_edges(primId, newer_than_date)
            if 'post_likes' in edge
        }
    else:
        secondary_EdgeCounts_in = {
            edge['fbid_source']: datastructs.EdgeCounts.from_dynamo(edge)
            for edge in dynamo.fetch_incoming_edges(primId, newer_than_date)
        }

    # dict of secondary id -> UserInfo:
    secondary_UserInfo = {
        user['fbid']: datastructs.UserInfo.from_dynamo(user)
        for user in dynamo.fetch_many_users(fbid for fbid in secondary_EdgeCounts_in)
    }

    if requireOutgoing:
        # build iterator of (secondary's Id, UserInfo, incoming edge, outgoing edge),
        # fetching outgoing edges from Dynamo. Then turn those into Edge objects,
        # while dropping outgoings that don't have a corresponding incoming for
        # whatever reason.
        data = (
            (
                edge.targetId,
                secondary_UserInfo.get(edge.targetId),
                secondary_EdgeCounts_in.get(edge.targetId),
                datastructs.EdgeCounts.from_dynamo(edge)
            )
            for edge in dynamo.fetch_outgoing_edges(primId, newer_than_date)
        )
    else:
        data = (
            (
                fbid,
                secondary_UserInfo.get(fbid),
                counts_in,
                None,
            )
            for fbid, counts_in in secondary_EdgeCounts_in.items()
        )

    edges = []
    for fbid, secondary, counts_in, counts_out in data:
        if secondary is None:
            logger.error(
                "Secondary %r found in edges but not in users",
                fbid
            )
            continue
        if counts_in is None:
            logger.warn(
                "Edge for user %r found in outgoing but not in incoming edges",
                fbid
            )
            continue
        edges.append(datastructs.Edge(primary, secondary, counts_in, counts_out))
    return edges
