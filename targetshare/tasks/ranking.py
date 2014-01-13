from __future__ import absolute_import
import logging
from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models.loading import get_model

from targetshare import models
from targetshare.integration import facebook
from targetshare.tasks import db

logger = get_task_logger(__name__)
rvn_logger = logging.getLogger('crow')
MIN_FRIEND_COUNT = 100
FRIEND_THRESHOLD_PERCENT = 90


def proximity_rank_three(mock_mode, fbid, token, **kwargs):
    ''' Builds the px3 crawl and filtering chain '''
    chain = (
        px3_crawl.s(mock_mode, fbid, token) |
        perform_filtering.s(fbid=fbid, **kwargs)
    )
    task = chain.apply_async()
    return task


@shared_task(default_retry_delay=1, max_retries=3)
def px3_crawl(mockMode, fbid, token):
    """Crawl and rank a user's network to proximity level three."""
    fb_client = facebook.mock_client if mockMode else facebook.client
    try:
        user = fb_client.get_user(fbid, token['token'])
        edges_unranked = fb_client.get_friend_edges(
            user,
            token['token'],
            require_incoming=False,
            require_outgoing=False
        )
    except IOError as exc:
        px3_crawl.retry(exc=exc)

    return models.datastructs.EdgeAggregate.rank(
        edges_unranked,
        require_incoming=False,
        require_outgoing=False,
    )


@shared_task
def perform_filtering(edgesRanked, campaignId, contentId, fbid, visit_id, numFace,
                      fallbackCount=0, already_picked=None,
                      visit_type='targetshare.Visit', cache_match=False):
    """Filter the given, ranked, Edges according to the configuration of the
    specified Campaign.

    """
    if fallbackCount > settings.MAX_FALLBACK_COUNT:
        # zzz Be more elegant here if cascading?
        raise RuntimeError("Exceeded maximum fallback count")

    app, model_name = visit_type.split('.')
    interaction = get_model(app, model_name).objects.get(pk=visit_id)

    campaign = models.relational.Campaign.objects.get(campaign_id=campaignId)
    client = campaign.client
    client_content = models.relational.ClientContent.objects.get(content_id=contentId)
    already_picked = already_picked or models.datastructs.TieredEdges()

    # Get fallback & threshold info about this campaign from the DB
    properties = campaign.campaignproperties.get()
    fallback_cascading = properties.fallback_is_cascading
    fallback_content_id = properties.fallback_content_id

    if properties.fallback_is_cascading and (properties.fallback_campaign is None):
        rvn_logger.error("Campaign %s expects cascading fallback, but fails to specify fallback campaign.",
                     campaignId)
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
    exclude_friends = set(models.relational.FaceExclusion.objects.filter(
        fbid=fbid,
        campaign=campaign,
        content=client_content,
    ).values_list('friend_fbid', flat=True))
    exclude_friends = exclude_friends.union(already_picked.secondary_ids)    # avoid re-adding if already picked
    edges_eligible = [
        edge for edge in edgesRanked if edge.secondary.fbid not in exclude_friends
    ]

    # Get filter experiments, do assignment (and write DB)
    global_filter = campaign.campaignglobalfilters.random_assign()
    interaction.assignments.create_managed(
        campaign=campaign,
        content=client_content,
        feature_row=global_filter,
        chosen_from_rows=campaign.campaignglobalfilters,
    )

    # apply filter
    filtered_edges = global_filter.filter_edges_by_sec(edges_eligible)

    # Get choice set experiments, do assignment (and write DB)
    campaign_choice_sets = campaign.campaignchoicesets.all()
    choice_set = campaign_choice_sets.random_assign()
    interaction.assignments.create_managed(
        campaign=campaign,
        content=client_content,
        feature_row=choice_set,
        chosen_from_rows=campaign.campaignchoicesets,
    )
    allow_generic = {
        option.choice_set.pk: [option.allow_generic, option.generic_url_slug]
        for option in campaign_choice_sets
    }[choice_set.pk]

    # pick best choice set filter (and write DB)
    bestCSFilter = None
    try:
        bestCSFilter = choice_set.choose_best_filter(
            filtered_edges, useGeneric=allow_generic[0],
            minFriends=minFriends, eligibleProportion=1.0,
            cache_match=cache_match
        )

        choice_set_slug = bestCSFilter[0].url_slug if bestCSFilter[0] else allow_generic[1]
        best_csf_id = bestCSFilter[0].filter_id if bestCSFilter[0] else None

        already_picked += models.datastructs.TieredEdges(
            edges=bestCSFilter[1],
            bestCSFilterId=best_csf_id,
            choiceSetSlug=choice_set_slug,
            campaignId=campaignId,
            contentId=contentId
        )
    except models.relational.ChoiceSet.TooFewFriendsError:
        rvn_logger.info("Too few friends found for %s with campaign %s. Checking for fallback.",
                    fbid, campaignId)

    if bestCSFilter:
        if bestCSFilter[0] is None:
            # We got generic...
            logger.debug("Generic returned for %s with campaign %s.", fbid, campaignId)
            interaction.assignments.create_managed(
                campaign=campaign,
                content=client_content,
                feature_row=None,
                random_assign=False,
                chosen_from_rows=choice_set.choicesetfilters,
                feature_type='generic choice set filter',
            )
        else:
            interaction.assignments.create_managed(
                campaign=campaign,
                content=client_content,
                feature_row=bestCSFilter[0].filter_id,
                random_assign=False,
                chosen_from_rows=choice_set.choicesetfilters,
            )

    slotsLeft = numFace - len(already_picked)

    if slotsLeft > 0 and fallback_cascading:
        # We still have slots to fill and can fallback to do so

        # write "fallback" assignments to DB
        interaction.assignments.create(
            campaign=campaign,
            content=client_content,
            feature_type='cascading fallback campaign',
            feature_row=properties.fallback_campaign.pk,
            chosen_from_table='campaign_properties',
            chosen_from_rows=[properties.pk],
            random_assign=False,
        )
        interaction.assignments.create(
            campaign=campaign,
            content=client_content,
            feature_type='cascading fallback content',
            feature_row=fallback_content_id,
            chosen_from_table='campaign_properties',
            chosen_from_rows=[properties.pk],
            random_assign=False,
        )

        # Recursive call with new fallbackCampaignId & fallback_content_id,
        # incrementing fallbackCount
        return perform_filtering(
            edgesRanked,
            properties.fallback_campaign.pk,
            fallback_content_id,
            fbid,
            visit_id,
            numFace,
            fallbackCount + 1,
            already_picked,
        )

    elif len(already_picked) < minFriends:
        # We haven't found enough friends to satisfy the campaign's
        # requirement, so need to fallback

        # if fallback campaign_id IS NULL, nothing we can do, so just return an error.
        if properties.fallback_campaign is None:
            # zzz Obviously, do something smarter here...
            rvn_logger.info(
                "No fallback for %s with campaign %s. Returning error to user.",
                fbid,
                campaignId
            )
            # zzz ideally, want this to be the full URL with
            #     flask.url_for(), but complicated with Celery...
            thisContent = '%s:button /frame_faces/%s/%s' % (
                client.fb_app_name,
                campaignId,
                contentId
            )
            interaction.events.create(
                campaign_id=campaignId,
                client_content_id=contentId,
                content=thisContent,
                event_type='no_friends_error'
            )
            return (None, None, None, None, campaignId, contentId)

        # write "fallback" assignments to DB
        interaction.assignments.create(
            campaign=campaign,
            content=client_content,
            feature_type='cascading fallback campaign',
            feature_row=properties.fallback_campaign.pk,
            chosen_from_table='campaign_properties',
            chosen_from_rows=[properties.pk],
            random_assign=False,
        )
        interaction.assignments.create(
            campaign=campaign,
            content=client_content,
            feature_type='fallback campaign',
            feature_row=fallback_content_id,
            chosen_from_table='campaign_properties',
            chosen_from_rows=[properties.pk],
            random_assign=False,
        )

        # If we're not cascading, no one is already picked.
        # If we're here, should probably always be the case that
        # fallback_cascading is False, but do the check to be safe...
        already_picked = already_picked if fallback_cascading else None

        # Recursive call with new fallbackCampaignId & fallback_content_id,
        # incrementing fallbackCount
        return perform_filtering(
            edgesRanked,
            properties.fallback_campaign.pk,
            fallback_content_id,
            fbid,
            visit_id,
            numFace,
            fallbackCount + 1,
            already_picked,
        )

    else:
        # We're done cascading and have enough friends, so time to return!

        # Might have cascaded beyond the point of having new friends to add,
        # so pick up various return values from the last tier with friends.
        last_tier = already_picked[-1]

        return (
            edgesRanked,
            already_picked,
            last_tier['bestCSFilterId'],
            last_tier['choiceSetSlug'],
            last_tier['campaignId'],
            last_tier['contentId'],
        )


@shared_task(default_retry_delay=1, max_retries=3)
def proximity_rank_four(mockMode, fbid, token):
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
