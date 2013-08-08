from __future__ import absolute_import
from datetime import timedelta

import celery
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from targetshare import (
    database,
    facebook,
    mock_facebook,
    models,
    ranking,
    utils,
)

MAX_FALLBACK_COUNT = 5
logger = get_task_logger(__name__)


@celery.task
def add(x, y):
    ''' Not really used, but helpful if you're testing out some of the
    zanier Celery tools.
    '''
    return x + y


def proximity_rank_three(mock_mode, fbid, token, **kwargs):
    ''' Builds the px3 crawl and filtering chain '''
    chain = (
        px3_crawl.s(mock_mode, fbid, token) |
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
    alreadyPicked = alreadyPicked or models.datastructs.TieredEdges()

    if (fallbackCount > MAX_FALLBACK_COUNT):
        # zzz Be more elegant here if cascading?
        raise RuntimeError("Exceeded maximum fallback count")

    # Get fallback & threshold info about this campaign from the DB
    properties = models.CampaignProperties.objects.get(campaign__pk=campaignId)
    fallback_cascading = properties.fallback_is_cascading
    fallback_content_id = properties.fallback_content_id

    if properties.fallback_is_cascading and (properties.fallback_campaign is None):
        logger.error("Campaign %s expects cascading fallback, but fails to specify fallback campaign.", campaignId)
        fallback_cascading = None

    # if fallback content_id IS NULL, defer to current content_id
    if (properties.fallback_content is None and
            properties.fallback_campaign is not None):
        fallback_content_id = contentId

    # For a cascading fallback, take any friends at all for
    # the current campaign to append to the list. Otherwise,
    # use the minFriends parameter as the threshold for errors.
    minFriends = 1 if fallback_cascading else properties.min_friends

    # Check if any friends should be excluded for this campaign/content combination
    exclude_friends = set(models.FaceExclusion.objects.filter(
        fbid=fbid,
        campaign__pk=campaignId,
        content__pk=contentId
    ).values_list('friend_fbid', flat=True))
    exclude_friends = exclude_friends.union(alreadyPicked.secondaryIds())    # avoid re-adding if already picked
    edges_eligible = [
        e for e in edgesRanked if e.secondary.id not in exclude_friends
    ]

    # Get filter experiments, do assignment (and write DB)
    filter_exp_tupes = sorted(models.CampaignGlobalFilter.objects.filter(
        campaign__pk=campaignId
    ).values_list('filter_id', 'rand_cdf'), key=lambda t: t[1])
    utils.check_cdf(filter_exp_tupes)
    global_filter_id = utils.rand_assign(filter_exp_tupes)
    models.Assignment.objects.create(
        session_id=sessionId, campaign_id=campaignId, content_id=contentId,
        feature_type='filter_id', feature_row=global_filter_id,
        random_assign=True, chosen_from_table='campaign_global_filters',
        chosen_from_rows=[r[0] for r in filter_exp_tupes]
    )

    # apply filter
    global_filter = models.Filter.objects.get(
        pk=global_filter_id)
    filtered_edges = global_filter.filter_edges_by_sec(edges_eligible)

    # Get choice set experiments, do assignment (and write DB)
    choice_set_recs = models.CampaignChoiceSet.objects.filter(
        campaign__pk=campaignId
    )
    choice_set_exp_tupes = [
        (r.choice_set_id, r.rand_cdf) for r in choice_set_recs
    ]
    choice_set_id = utils.rand_assign(choice_set_exp_tupes)
    models.Assignment.objects.create(
        session_id=sessionId, campaign_id=campaignId, content_id=contentId,
        feature_type='choice_set_id', feature_row=choice_set_id,
        random_assign=True, chosen_from_table='campaign_choice_sets',
        chosen_from_rows=[r.pk for r in choice_set_recs]
    )
    allow_generic = {
        r.choice_set.pk: [r.allow_generic, r.generic_url_slug] for r in choice_set_recs
    }[choice_set_id]

    # pick best choice set filter (and write DB)
    choice_set = models.ChoiceSet.objects.get(pk=choice_set_id)
    bestCSFilter = None
    try:
        bestCSFilter = choice_set.choose_best_filter(
            filtered_edges, useGeneric=allow_generic[0],
            minFriends=minFriends, eligibleProportion=1.0
        )

        choice_set_slug = bestCSFilter[0].url_slug if bestCSFilter[0] else allow_generic[1]
        best_csf_id = bestCSFilter[0].filter_id if bestCSFilter[0] else None

        alreadyPicked.appendTier(
            edges=bestCSFilter[1],
            bestCSFilterId=best_csf_id,
            choiceSetSlug=choice_set_slug,
            campaignId=campaignId,
            contentId=contentId
        )
    except utils.TooFewFriendsError as e:
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
            models.Assignment.objects.create(
                session_id=sessionId, campaign_id=campaignId, content_id=contentId,
                feature_type='generic choice set filter',
                feature_row=None, random_assign=False,
                chosen_from_table='choice_set_filters',
                chosen_from_rows=[x.pk for x in choice_set.choicesetfilter_set.all()]
            )
        else:
            models.Assignment.objects.create(
                session_id=sessionId, campaign_id=campaignId, content_id=contentId,
                feature_type='filter_id', feature_row=bestCSFilter[0].filter_id,
                random_assign=False, chosen_from_table='choice_set_filters',
                chosen_from_rows=[x.pk for x in choice_set.choicesetfilters.all()]
            )

    slotsLeft = int(numFace) - len(alreadyPicked)

    if slotsLeft > 0 and fallback_cascading:
        # We still have slots to fill and can fallback to do so

        # write "fallback" assignments to DB
        models.Assignment.objects.create(
            session_id=sessionId, campaign_id=campaignId, content_id=contentId,
            feature_type='cascading fallback campaign',
            feature_row=properties.fallback_campaign.pk,
            random_assign=False, chosen_from_table='campaign_properties',
            chosen_from_rows=[properties.pk]
        )
        models.Assignment.objects.create(
            session_id=sessionId, campaign_id=campaignId, content_id=contentId,
            feature_type='cascading fallback content ',
            feature_row=fallback_content_id,
            random_assign=False, chosen_from_table='campaign_properties',
            chosen_from_rows=[properties.pk]
        )

        # Recursive call with new fallbackCampaignId & fallback_content_id,
        # incrementing fallbackCount
        return perform_filtering(
            edgesRanked, clientSubdomain, properties.fallback_campaign.pk,
            fallback_content_id, sessionId, ip, fbid, numFace,
            paramsDB, fallbackCount + 1, alreadyPicked
        )

    elif len(alreadyPicked) < minFriends:
        # We haven't found enough friends to satisfy the campaign's
        # requirement, so need to fallback

        # if fallback campaign_id IS NULL, nothing we can do, so just return an error.
        if properties.fallback_campaign is None:
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
            models.Event.objects.create(
                session_id=sessionId, campaign_id=campaignId,
                client_content_id=contentId, ip=ip, fbid=fbid,
                friend_fbid=None, event_type='no_friends_error',
                app_id=int(paramsDB[1]), content=thisContent,
                activity_id=None
            )
            return (None, None, None, None, campaignId, contentId)

        # write "fallback" assignments to DB
        models.Assignment.objects.create(
            session_id=sessionId, campaign_id=campaignId, content_id=contentId,
            feature_type='cascading fallback campaign',
            feature_row=properties.fallback_campaign.pk,
            random_assign=False, chosen_from_table='campaign_properties',
            chosen_from_rows=[properties.pk]
        )
        models.Assignment.objects.create(
            session_id=sessionId, campaign_id=campaignId, content_id=contentId,
            feature_type='fallback campaign',
            feature_row=fallback_content_id,
            random_assign=False, chosen_from_table='campaign_properties',
            chosen_from_rows=[properties.pk]
        )

        # If we're not cascading, no one is already picked.
        # If we're here, should probably always be the case that
        # fallback_cascading is False, but do the check to be safe...
        alreadyPicked = alreadyPicked if fallback_cascading else None

        # Recursive call with new fallbackCampaignId & fallback_content_id,
        # incrementing fallbackCount
        return perform_filtering(
            edgesRanked, clientSubdomain, properties.fallback_campaign.pk,
            fallback_content_id, sessionId, ip, fbid, numFace,
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
        newer_than = timezone.now() + timedelta(days=settings.FRESHNESS)
        # FIXME: When PX5 comes online, this getFriendEdgesDb call could return
        # insufficient results from the px5 crawls. We'll need to check the
        # length of the edges list against a friends count from FB.
        edgesUnranked = models.Edge.objects.filter(
            fbid_target=fbid,
            post_likes__isnull=False,
            updated__gte=newer_than
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
                      background=settings.DATABASES.default.BACKGROUND_WRITE)
    return edgesRanked
