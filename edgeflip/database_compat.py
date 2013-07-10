"""Compatability layer for `edgeflip.database`


This module imports _everything_ from `edgeflip.database`, and then overrides
some functions with versions backed by `edgeflip.dynamo`. See their
respective documentations.
"""
# slurp database's namespace before other imports, so we can overwrite
from .database import *

import logging
import threading

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


def updateTokensDb(users, token):
    """update tokens table"""
    raise NotImplementedError()

def updateTokensDb2(token):
    """update tokens table

    :arg token: a `datastruct.TokenInfo`
    """

    save_token(token.ownerId, token.appId, token.tok, token.expires)


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


# helper function that may get run in a background thread
def _updateDb(user, token, edges):
    """takes datastructs.* and writes to database
    """
    tim = datastructs.Timer()

    # update token for primary
    updateTokensDb([user], token)
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
