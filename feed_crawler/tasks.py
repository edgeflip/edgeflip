from __future__ import absolute_import
from datetime import timedelta

import celery
from celery.utils.log import get_task_logger
from django.conf import settings

from targetshare import models
from targetshare.integration import facebook
from targetshare.tasks import db

logger = get_task_logger(__name__)
MIN_FRIEND_COUNT = 100
FRIEND_THRESHOLD_PERCENT = 90


@celery.task(default_retry_delay=1, max_retries=3)
def background_px4(mockMode, fbid, token):
    """Crawl and rank a user's network to proximity level four, and persist the
    User, secondary Users, Token and Edges to the database.


    Under 100 people, just go to FB and get the best data
    Over 100 people, let's make sure Dynamo has at least 90 percent

    """
    fb_client = facebook.mock_client if mockMode else facebook.client
    try:
        user = fb_client.get_user(fbid, token['token'])
        friend_count = fb_client.get_friend_count(fbid, token['token'])
        if friend_count < MIN_FRIEND_COUNT:
            logger.info(
                'FBID {}: Has less than 100 friends, hitting FB'.format(fbid)
            )
            edges_unranked = fb_client.get_friend_edges(
                user,
                token['token'],
                require_incoming=True,
                require_outgoing=False,
            )
        else:
            edges_unranked = models.datastructs.Edge.get_friend_edges(
                user,
                require_incoming=True,
                require_outgoing=False,
                max_age=timedelta(days=settings.FRESHNESS),
            )
            if (not friend_count or
                    ((float(len(edges_unranked)) / friend_count) * 100) < FRIEND_THRESHOLD_PERCENT):
                logger.info(
                    'FBID {}: Has {} FB Friends, found {} in Dynamo. Falling back to FB'.format(
                        fbid, friend_count, len(edges_unranked)
                    )
                )
                edges_unranked = fb_client.get_friend_edges(
                    user,
                    token['token'],
                    require_incoming=True,
                    require_outgoing=False,
                )
            else:
                logger.info(
                    'FBID {}: Has {} FB Friends, found {} in Dynamo, using Dynamo data.'.format(
                        fbid, friend_count, len(edges_unranked)
                    )
                )
    except IOError as exc:
        proximity_rank_four.retry(exc=exc)

    edges_ranked = models.datastructs.EdgeAggregate.rank(
        edges_unranked,
        require_incoming=True,
        require_outgoing=False,
    )

    db.delayed_save.delay(token, overwrite=True)
    db.upsert.delay(user)
    db.upsert.delay([edge.secondary for edge in edges_ranked])
    db.update_edges.delay(edges_ranked)

    return edges_ranked
