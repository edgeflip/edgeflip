from __future__ import absolute_import
from urllib2 import HTTPError

from edgeflip import (
    database,
    facebook,
    mock_facebook,
    ranking,
)
from edgeflip.celery import celery
from edgeflip.settings import config


@celery.task
def retrieve_fb_user_info(mock_mode, fbid, token):
    ''' Retrieves FB user info and performs px3 edge ranking '''
    try:
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
        database.updateDb(user, token, edgesRanked,
                        background=config.database.use_threads)
    except HTTPError:
        retrieve_fb_user_info.retry()

    return (user, edgesRanked)
