from __future__ import absolute_import
import time

import flask
from celery.utils.log import get_task_logger

from edgeflip import (
    client_db_tools as cdb,
    database,
    facebook,
    mock_facebook,
    ranking,
)
from edgeflip.celery import celery
from edgeflip.settings import config

MAX_FALLBACK_COUNT = 5
logger = get_task_logger(__name__)


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


@celery.task(default_retry_delay=1, max_retries=3)
def px3_crawl(mockMode, fbid, token):
    ''' Performs the standard px3 crawl '''
    fbmodule = mock_facebook if mockMode else facebook
    try:
        edgesUnranked = fbmodule.getFriendEdgesFb(
            fbid,
            token.tok,
            requireIncoming=False,
            requireOutgoing=False
        )
    except IOError as exc:
        px3_crawl.retry(exc=exc)

    edgesRanked = ranking.getFriendRanking(
        edgesUnranked,
        requireIncoming=False,
        requireOutgoing=False,
    )
    return edgesRanked


@celery.task
def perform_filtering(edgesRanked, clientSubdomain, campaignId, contentId,
                      sessionId, ip, fbid, numFace, paramsDB,
                      fallbackCount=0, alreadyPicked=None):
    ''' Performs the filtering that web.sharing.applyCampaign formerly handled
    in the past.
    '''

    alreadyPicked = alreadyPicked if alreadyPicked else cdb.TieredEdges()

    if (fallbackCount > MAX_FALLBACK_COUNT):
        # zzz Be more elegant here if cascading?
        raise RuntimeError("Exceeded maximum fallback count")

    # Get fallback & threshold info about this campaign from the DB
    cmpgPropsId, fallbackCampaignId, fallbackContentId, fallbackCascading, minFriends = cdb.dbGetObjectAttributes(
        'campaign_properties',
        ['campaign_property_id', 'fallback_campaign_id', 'fallback_content_id',
         'fallback_is_cascading', 'min_friends'],
        'campaign_id',
        campaignId
    )[0]

    if fallbackCascading and (fallbackCampaignId is None):
        logger.error("Campaign %s expects cascading fallback, but fails to specify fallback campaign.", campaignId)
        fallbackCascading = None

    # if fallback content_id IS NULL, defer to current content_id
    if (fallbackContentId is None) and (fallbackCampaignId is not None):
        fallbackContentId = contentId

    # For a cascading fallback, take any friends at all for
    # the current campaign to append to the list. Otherwise,
    # use the minFriends parameter as the threshold for errors.
    minFriends = 1 if fallbackCascading else minFriends

    # Check if any friends should be excluded for this campaign/content combination
    excludeFriends = database.getFaceExclusionsDb(fbid, campaignId, contentId)
    excludeFriends = excludeFriends.union(alreadyPicked.secondaryIds())    # avoid re-adding if already picked
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
    bestCSFilter = None
    try:
        bestCSFilter = choiceSet.chooseBestFilter(
            filteredEdges, useGeneric=allowGeneric[0],
            minFriends=minFriends, eligibleProportion=1.0
        )

        choiceSetSlug = bestCSFilter[0].urlSlug if bestCSFilter[0] else allowGeneric[1]
        bestCSFilterId = bestCSFilter[0].filterId if bestCSFilter[0] else None

        alreadyPicked.appendTier(
            edges=bestCSFilter[1],
            bestCSFilterId=bestCSFilterId,
            choiceSetSlug=choiceSetSlug,
            campaignId=campaignId,
            contentId=contentId
        )
    except cdb.TooFewFriendsError as e:
        logger.info(
            "Too few friends found for %s with campaign %s. Checking for fallback.",
            fbid,
            campaignId
        )
        pass

    if bestCSFilter:
        if (bestCSFilter[0] is None):
            # We got generic...
            logger.debug("Generic returned for %s with campaign %s." % (
                fbid, campaignId
            ))
            cdb.dbWriteAssignment(
                sessionId, campaignId, contentId,
                'generic choice set filter', None, False,
                'choice_set_filters',
                [csf.choiceSetFilterId for csf in choiceSet.choiceSetFilters],
                background=config.database.use_threads
            )
        else:
            cdb.dbWriteAssignment(
                sessionId, campaignId, contentId, 'filter_id',
                bestCSFilter[0].filterId, False, 'choice_set_filters',
                [csf.choiceSetFilterId for csf in choiceSet.choiceSetFilters],
                background=config.database.use_threads
            )

    slotsLeft = numFace - len(alreadyPicked)

    if slotsLeft > 0 and fallbackCascading:
        # We still have slots to fill and can fallback to do so

        # write "fallback" assignments to DB
        cdb.dbWriteAssignment(
            sessionId, campaignId, contentId, 'cascading fallback campaign',
            fallbackCampaignId, False, 'campaign_properties', [cmpgPropsId],
            background=config.database.use_threads
        )
        cdb.dbWriteAssignment(
            sessionId, campaignId, contentId, 'cascading fallback content',
            fallbackContentId, False, 'campaign_properties', [cmpgPropsId],
            background=config.database.use_threads
        )

        # Recursive call with new fallbackCampaignId & fallbackContentId,
        # incrementing fallbackCount
        return perform_filtering(
            edgesRanked, clientSubdomain, fallbackCampaignId,
            fallbackContentId, sessionId, ip, fbid, numFace,
            paramsDB, fallbackCount + 1, alreadyPicked
        )

    elif len(alreadyPicked) < minFriends:
        # We haven't found enough friends to satisfy the campaign's
        # requirement, so need to fallback

        # if fallback campaign_id IS NULL, nothing we can do, so just return an error.
        if (fallbackCampaignId is None):
            # zzz Obviously, do something smarter here...
            logger.info(
                "No fallback for %s with campaign %s. Returning error to user.",
                fbid,
                campaignId
            )
            # zzz ideally, want this to be the full URL with
            #     flask.url_for(), but complicated with Celery...
            thisContent = '%s:button %s' % (
                paramsDB[0],
                '/frame_faces/%s/%s' % (campaignId, contentId)
            )
            database.writeEventsDb(
                sessionId, campaignId, contentId, ip, fbid, [None],
                'no_friends_error', int(paramsDB[1]), thisContent, None,
                background=config.database.use_threads
            )
            return (None, None, None, None, campaignId, contentId)

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

        # If we're not cascading, no one is already picked.
        # If we're here, should probably always be the case that
        # fallbackCascading is False, but do the check to be safe...
        alreadyPicked = alreadyPicked if fallbackCascading else None

        # Recursive call with new fallbackCampaignId & fallbackContentId,
        # incrementing fallbackCount
        return perform_filtering(
            edgesRanked, clientSubdomain, fallbackCampaignId,
            fallbackContentId, sessionId, ip, fbid, numFace,
            paramsDB, fallbackCount + 1, alreadyPicked
        )

    else:
        # We're done cascading and have enough friends, so time to return!

        # Might have cascaded beyond the point of having new friends to add,
        # so pick up various return values from the last tier with friends.
        last_tier = alreadyPicked.tiers[-1]

        return (
            edgesRanked, alreadyPicked,
            last_tier['bestCSFilterId'], last_tier['choiceSetSlug'],
            last_tier['campaignId'], last_tier['contentId']
        )


@celery.task(default_retry_delay=1, max_retries=3)
def proximity_rank_four(mockMode, fbid, token):
    ''' Performs the px4 crawling '''
    fbmodule = mock_facebook if mockMode else facebook
    try:
        user = fbmodule.getUserFb(fbid, token.tok)
        newerThan = time.time() - config.freshness * 24 * 60 * 60
        # FIXME: When PX5 comes online, this getFriendEdgesDb call could return
        # insufficient results from the px5 crawls. We'll need to check the
        # length of the edges list against a friends count from FB.
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
    except IOError as exc:
        proximity_rank_four.retry(exc=exc)

    edgesRanked = ranking.getFriendRanking(
        edgesUnranked,
        requireIncoming=True,
        requireOutgoing=False,
    )
    database.updateDb(user, token, edgesRanked,
                      background=config.database.use_threads)
    return edgesRanked
