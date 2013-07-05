from __future__ import absolute_import
import time
import logging

import flask

from edgeflip import (
    client_db_tools as cdb,
    database,
    facebook,
    mock_facebook,
    ranking,
)
from edgeflip.celery import celery
from edgeflip.settings import config

MAX_FALLBACK_COUNT = 3
logger = logging.getLogger(__name__)


@celery.task
def add(x, y):
    ''' Not really used, but helpful if you're testing out some of the
    zanier Celery tools.
    '''
    return x + y


def proximity_rank_three(mockMode, fbid, token, **kwargs):
    ''' Builds the px3 crawl and filtering chain '''
    chain = (
        px3_crawl.s(mockMode, fbid, token) |
        perform_filtering.s(fbid=fbid, **kwargs)
    )
    task = chain.apply_async()
    return task.id


@celery.task
def px3_crawl(mockMode, fbid, token):
    ''' Performs the standard px3 crawl '''
    fbmodule = mock_facebook if mockMode else facebook
    edgesUnranked = fbmodule.getFriendEdgesFb(
        fbid,
        token.tok,
        requireIncoming=False,
        requireOutgoing=False
    )
    edgesRanked = ranking.getFriendRanking(
        edgesUnranked,
        requireIncoming=False,
        requireOutgoing=False,
    )
    return edgesRanked


@celery.task
def perform_filtering(edgesRanked, clientSubdomain, campaignId, contentId,
                      sessionId, ip, fbid, numFace, paramsDB,
                      fallbackCount=0):
    ''' Performs the filtering that web.sharing.applyCampaign formerly handled
    in the past.
    '''

    if (fallbackCount > MAX_FALLBACK_COUNT):
        raise RuntimeError("Exceeded maximum fallback count")

    # Check if any friends should be excluded for this campaign/content combination
    excludeFriends = database.getFaceExclusionsDb(fbid, campaignId, contentId)
    edgesEligible = [
        e for e in edgesRanked if e.secondary.id not in excludeFriends
    ]

    # Get filter experiments, do assignment (and write DB)
    filterRecs = cdb.dbGetExperimentTupes(
        'campaign_global_filters', 'campaign_global_filter_id',
        'filter_id', [('campaign_id', campaignId)]
    )
    filterExpTupes = [(r[1], r[2]) for r in filterRecs]
    globalFilterId = cdb.doRandAssign(filterExpTupes)
    cdb.dbWriteAssignment(
        sessionId, campaignId, contentId, 'filter_id', globalFilterId, True,
        'campaign_global_filters', [r[0] for r in filterRecs],
        background=config.database.use_threads
    )

    # apply filter
    globalFilter = cdb.getFilter(globalFilterId)
    filteredEdges = globalFilter.filterEdgesBySec(edgesEligible)

    # Get choice set experiments, do assignment (and write DB)
    choiceSetRecs = cdb.dbGetExperimentTupes(
        'campaign_choice_sets', 'campaign_choice_set_id', 'choice_set_id',
        [('campaign_id', campaignId)], ['allow_generic', 'generic_url_slug']
    )
    choiceSetExpTupes = [(r[1], r[2]) for r in choiceSetRecs]
    choiceSetId = cdb.doRandAssign(choiceSetExpTupes)
    cdb.dbWriteAssignment(
        sessionId, campaignId, contentId, 'choice_set_id', choiceSetId, True,
        'campaign_choice_sets', [r[0] for r in filterRecs],
        background=config.database.use_threads
    )
    allowGeneric = {r[1]: [r[3], r[4]] for r in choiceSetRecs}[choiceSetId]

    # pick best choice set filter (and write DB)
    choiceSet = cdb.getChoiceSet(choiceSetId)
    try:
        bestCSFilter = choiceSet.chooseBestFilter(
            filteredEdges, useGeneric=allowGeneric[0],
            minFriends=1, eligibleProportion=1.0
        )
    except cdb.TooFewFriendsError as e:
        logger.info(
            "Too few friends found for %s with campaign %s. Checking for fallback.",
            fbid,
            campaignId
        )

        # Get fallback campaign_id and content_id from DB
        cmpgPropsId, fallbackCampaignId, fallbackContentId = cdb.dbGetObjectAttributes(
            'campaign_properties',
            ['campaign_property_id', 'fallback_campaign_id', 'fallback_content_id'],
            'campaign_id',
            campaignId
        )[0]
        # if fallback campaign_id IS NULL, nothing we can do, so just return an error.

        if (fallbackCampaignId is None):
            # zzz Obviously, do something smarter here...
            logger.info(
                "No fallback for %s with campaign %s. Returning error to user.",
                fbid,
                campaignId
            )
            thisContent = '%s:button %s' % (
                paramsDB[0],
                flask.url_for(
                    'frame_faces', campaignId=campaignId,
                    contentId=contentId, _external=True
                )
            )
            database.writeEventsDb(
                sessionId, campaignId, contentId, ip, fbid, [None],
                'no_friends_error', int(paramsDB[1]), thisContent, None,
                background=config.database.use_threads
            )
            return (None, None, None, None)

        # if fallback content_id IS NULL, defer to current content_id
        if (fallbackContentId is None):
            fallbackContentId = contentId

        # write "fallback" assignments to DB
        cdb.dbWriteAssignment(
            sessionId, campaignId, contentId, 'fallback campaign',
            fallbackCampaignId, False, 'campaign_properties', [cmpgPropsId],
            background=config.database.use_threads
        )
        cdb.dbWriteAssignment(
            sessionId, campaignId, contentId, 'fallback content',
            fallbackContentId, False, 'campaign_properties', [cmpgPropsId],
            background=config.database.use_threads
        )

        # Recursive call with new fallbackCampaignId & fallbackContentId,
        # incrementing fallbackCount
        return perform_filtering(
            edgesRanked, clientSubdomain, fallbackCampaignId,
            fallbackContentId, sessionId, ip, fbid, numFace,
            paramsDB, fallbackCount + 1
        )

    # Can't pickle lambdas and we don't need them anymore anyways
    bestCSFilter[0].str_func = None
    choiceSet.sortFunc = None
    return edgesRanked, bestCSFilter, choiceSet, allowGeneric


@celery.task
def proximity_rank_four(mockMode, fbid, token):
    ''' Performs the px4 crawling '''
    fbmodule = mock_facebook if mockMode else facebook
    user = fbmodule.getUserFb(fbid, token.tok)
    newerThan = time.time() - config.freshness * 24 * 60 * 60
    edgesUnranked = database.getFriendEdgesDb(
        fbid,
        requireIncoming=True,
        requireOutgoing=False,
        newerThan=newerThan
    )
    if not edgesUnranked:
        edgesUnranked = fbmodule.getFriendEdgesFb(
            fbid,
            token.tok,
            requireIncoming=True,
            requireOutgoing=False
        )
    edgesRanked = ranking.getFriendRanking(
        edgesUnranked,
        requireIncoming=True,
        requireOutgoing=False,
    )
    database.updateDb(user, token, edgesRanked,
                      background=config.database.use_threads)
    return edgesRanked
