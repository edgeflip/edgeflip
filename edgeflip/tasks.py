from __future__ import absolute_import
import logging

from edgeflip.celery import celery
from edgeflip import (
    database,
    facebook,
    mock_facebook,
    ranking,
)

MAX_FALLBACK_COUNT = 3 # TODO: Move to config?
logger = logging.getLogger(__name__)


@celery.task
def retrieve_fb_user_info(mock_mode, fbid, token):
    ''' Retrieves FB user info and performs px3 edge ranking '''
    if mock_mode:
        fbmodule = mock_facebook
    else:
        fbmodule = facebook
    user = fbmodule.getUserFb(fbid, token.tok)
    edgesUnranked = fbmodule.getFriendEdgesFb(
        fbid,
        token.tok,
        requireIncoming=False,
        requireOutgoing=False
    )
    edgesRanked = ranking.getFriendRanking(
        edgesUnranked, requireIncoming=False, requireOutgoing=False)
    database.updateDb(user, token, edgesRanked)
    return edgesRanked
