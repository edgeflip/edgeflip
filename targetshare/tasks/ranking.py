from __future__ import absolute_import
from collections import namedtuple
from datetime import timedelta

import celery
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models.loading import get_model

from targetshare import models
from targetshare.integration import facebook
from targetshare.tasks import db

LOG = get_task_logger(__name__)

DB_MIN_FRIEND_COUNT = 100
DB_FRIEND_THRESHOLD = 90 # percent


FilteringResult = namedtuple('FilteringResult', [
    'ranked',
    'filtered',
    'cs_filter_id',
    'choice_set_slug',
    'campaign_id',
    'content_id',
])

empty_filtering_result = FilteringResult._make((None,) * 6)


def proximity_rank_three(token, **filtering_args):
    """Build the px3 crawl-and-filter chain."""
    chain = (
        px3_crawl.s(token) |
        perform_filtering.s(fbid=token.fbid, **filtering_args)
    )
    return chain.apply_async()


@celery.task(default_retry_delay=1, max_retries=3)
def px3_crawl(token):
    """Crawl and rank a user's network to proximity level three."""
    try:
        user = facebook.client.get_user(token.fbid, token.token)
        edges_unranked = facebook.client.get_friend_edges(
            user,
            token.token,
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


@celery.task
def perform_filtering(edges_ranked, campaign_id, content_id, fbid, visit_id, num_faces,
                      fallback_count=0, already_picked=None,
                      px_rank=3, visit_type='targetshare.Visit', cache_match=False):
    """Filter the given, ranked, Edges according to the configuration of the
    specified Campaign.

    """
    if fallback_count > settings.MAX_FALLBACK_COUNT:
        raise RuntimeError("Exceeded maximum fallback count")

    app, model_name = visit_type.split('.')
    interaction = get_model(app, model_name).objects.get(pk=visit_id)

    client_content = models.relational.ClientContent.objects.get(content_id=content_id)
    campaign = models.relational.Campaign.objects.get(campaign_id=campaign_id)
    client = campaign.client
    properties = campaign.campaignproperties.get()
    fallback_cascading = properties.fallback_is_cascading
    fallback_content_id = properties.fallback_content_id
    already_picked = already_picked or models.datastructs.TieredEdges()

    if properties.fallback_is_cascading and properties.fallback_campaign is None:
        LOG.error("Campaign %s expects cascading fallback, but fails to specify fallback campaign.",
                  campaign_id)
        fallback_cascading = None

    # If fallback content_id IS NULL, defer to current content_id:
    if properties.fallback_content is None and properties.fallback_campaign is not None:
        fallback_content_id = content_id

    # For a cascading fallback, take any friends at all for
    # the current campaign to append to the list. Otherwise,
    # use the min_friends parameter as the threshold for errors.
    min_friends = 1 if fallback_cascading else properties.min_friends

    # Check if any friends should be excluded for this campaign/content combination
    exclude_friends = set(models.relational.FaceExclusion.objects.filter(
        fbid=fbid,
        campaign=campaign,
        content=client_content,
    ).values_list('friend_fbid', flat=True))
    # avoid re-adding if already picked:
    exclude_friends = exclude_friends.union(already_picked.secondary_ids)
    edges_eligible = [
        edge for edge in edges_ranked if edge.secondary.fbid not in exclude_friends
    ]

    # Assign filter experiments (and record) #

    # Apply global filter
    global_filter = campaign.campaignglobalfilters.random_assign()
    interaction.assignments.create_managed(
        campaign=campaign,
        content=client_content,
        feature_row=global_filter,
        chosen_from_rows=campaign.campaignglobalfilters,
    )
    # NOTE: This differs from how we handle px4 features on ChoiceSetFilters.
    # For px3, we exclude ChoiceSetFilters with px4 features entirely;
    # however, the global filter cannot be excluded.
    # For now, we'll simply ignore super-ranked features on the global filter,
    # though we might want to revisit this, (and e.g. raise an exception).
    edges_filtered = global_filter.filterfeatures.filter(
        feature_type__px_rank__lte=px_rank,
    ).filter_edges(edges_eligible)

    # Assign choice set experiments (and record)
    campaign_choice_sets = campaign.campaignchoicesets.all()
    choice_set = campaign_choice_sets.random_assign()
    interaction.assignments.create_managed(
        campaign=campaign,
        content=client_content,
        feature_row=choice_set,
        chosen_from_rows=campaign.campaignchoicesets,
    )
    (allow_generic, generic_slug) = campaign_choice_sets.values_list(
        'allow_generic', 'generic_url_slug'
    ).get(choice_set=choice_set)

    # Pick (and record) best choice set filter
    # TODO: email Rayid about this logic (and above)
    # TODO: test this query
    # Exclude ChoiceSetFilters written for super-ranked features:
    choice_set_filters = choice_set.choicesetfilters.exclude(
        filter__filterfeatures__feature_type__px_rank__gt=px_rank
    )
    try:
        (best_csf, best_csf_edges) = choice_set_filters.choose_best_filter(
            edges_filtered,
            use_generic=allow_generic,
            min_friends=min_friends,
            cache_match=cache_match,
        )
    except models.relational.ChoiceSetFilter.TooFewFriendsError:
        LOG.info("Too few friends found for %s with campaign %s. (Will check for fallback.)",
                 fbid, campaign_id)
    else:
        already_picked += models.datastructs.TieredEdges(
            edges=best_csf_edges,
            campaign_id=campaign_id,
            content_id=content_id,
            cs_filter_id=(best_csf.filter_id if best_csf else None),
            choice_set_slug=(best_csf.url_slug if best_csf else generic_slug),
        )
        if best_csf is None:
            # We got generic:
            LOG.debug("Generic returned for %s with campaign %s.", fbid, campaign_id)
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
                feature_row=best_csf.filter_id,
                random_assign=False,
                chosen_from_rows=choice_set.choicesetfilters,
            )

    slots_left = num_faces - len(already_picked)
    if slots_left > 0 and fallback_cascading:
        # We still have slots to fill and can fallback to do so

        # Record "fallback" assignments:
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

        # Recursive call with new campaign & content, incrementing fallback_count:
        return perform_filtering(
            edges_ranked,
            properties.fallback_campaign.pk,
            fallback_content_id,
            fbid,
            visit_id,
            num_faces,
            fallback_count + 1,
            already_picked,
            px_rank,
            visit_type,
            cache_match,
        )

    elif len(already_picked) < min_friends:
        # We haven't found enough friends to satisfy the campaign's
        # requirement, so need to fallback

        # if fallback campaign_id IS NULL, nothing we can do, so just return an error.
        if properties.fallback_campaign is None:
            LOG.error("No fallback for %s with campaign %s. (Will return error to user.)",
                      fbid, campaign_id)
            event_content = '{}:button /frame_faces/{}/{}'.format(
                client.fb_app_name,
                campaign_id,
                content_id,
            )
            interaction.events.create(
                campaign_id=campaign_id,
                client_content_id=content_id,
                content=event_content,
                event_type='no_friends_error'
            )
            return empty_filtering_result._replace(campaign_id=campaign_id,
                                                   content_id=content_id)

        # Record "fallback" assignments:
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

        # Recursive call with new campaign & content, incrementing fallback_count:
        return perform_filtering(
            edges_ranked,
            properties.fallback_campaign.pk,
            fallback_content_id,
            fbid,
            visit_id,
            num_faces,
            fallback_count + 1,
            already_picked,
            px_rank,
            visit_type,
            cache_match,
        )

    else:
        # We're done cascading and have enough friends, so time to return!

        # Might have cascaded beyond the point of having new friends to add,
        # so pick up various return values from the last tier with friends.
        last_tier = already_picked[-1]
        return FilteringResult(edges_ranked, already_picked, **last_tier)


def proximity_rank_four(token, **filtering_args):
    """Build the px4 crawl-and-refine chain."""
    chain = (
        px4_crawl.s(token) |
        refine_ranking.s(fbid=token.fbid, **filtering_args)
    )
    return chain.apply_async()


@celery.task(default_retry_delay=1, max_retries=3)
def px4_crawl(token):
    """Crawl and rank a user's network to proximity level four, and persist the
    User, secondary Users, Token and Edges to the database.

    Under 100 people, just go to FB and get the best data;
    over 100 people, let's make sure Dynamo has at least 90 percent.

    """
    try:
        user = facebook.client.get_user(token.fbid, token.token)
        friend_count = facebook.client.get_friend_count(token.fbid, token.token)
        if friend_count >= DB_MIN_FRIEND_COUNT:
            edges_unranked = models.datastructs.Edge.get_friend_edges(
                user,
                require_incoming=True,
                require_outgoing=False,
                max_age=timedelta(days=settings.FRESHNESS),
            )
            if (
                not friend_count or
                100.0 * len(edges_unranked) / friend_count >= DB_FRIEND_THRESHOLD
            ):
                LOG.info('FBID %r: Has %r FB Friends, found %r in Dynamo; using Dynamo data.',
                         token.fbid, friend_count, len(edges_unranked))
            else:
                LOG.info('FBID %r: Has %r FB Friends, found %r in Dynamo; falling back to FB',
                         token.fbid, friend_count, len(edges_unranked))
                edges_unranked = None
        else:
            LOG.info('FBID %r: Has %r friends, hitting FB', token.fbid, friend_count)
            edges_unranked = None

        hit_fb = edges_unranked is None
        if hit_fb:
            edges_unranked = facebook.client.get_friend_edges(
                user,
                token.token,
                require_incoming=True,
                require_outgoing=False,
            )
    except IOError as exc:
        px4_crawl.retry(exc=exc)

    edges_ranked = models.datastructs.EdgeAggregate.rank(
        edges_unranked,
        require_incoming=True,
        require_outgoing=False,
    )

    db.delayed_save.delay(token, overwrite=True)
    db.upsert.delay(user)
    db.upsert.delay([edge.secondary for edge in edges_ranked])
    db.update_edges.delay(edges_ranked)

    return (edges_ranked, hit_fb)


@celery.task
def refine_ranking(crawl_result, campaign_id, content_id, fbid, visit_id, num_faces,
                   visit_type='targetshare.Visit', cache_match=False):
    """Refine the px4 edge ranking and, depending on the crawl task, apply filtering.

    Filtering is achieved through the `perform_filtering` task, and so edges are
    filtered and campaign fallbacks are applied; however, to avoid timing out on
    large user networks, filtering is deferred to px3 unless the px4 crawl task
    has indicated that it did not attempt communication with Facebook or if the
    network is sufficiently small.

    """
    (edges_ranked, hit_fb) = crawl_result

    # TODO: rank-refinement
    # TODO: Should proximity rank be primary key? Or last (most minor) key? Or
    # TODO: should RankingKeys affect the proximity score, s.t. we rank by it,
    # TODO: (rather than overriding it)?

    px4_filters = models.relational.Filter.objects.filter(
        client__campaigns__campaign_id=campaign_id,
        filterfeatures__feature_type__px_rank__gte=4,
    )
    # TODO: Is this threshold sensible?
    if (not hit_fb or len(edges_ranked) < DB_MIN_FRIEND_COUNT) and px4_filters.exists():
        # We haven't wasted time hitting Facebook or user has few enough
        # friends that we should be able to apply refined filters anyway:
        return perform_filtering(
            edges_ranked, campaign_id, content_id, fbid, visit_id, num_faces,
            px_rank=4, visit_type=visit_type, cache_match=cache_match
        )
    else:
        # Use empty result to indicate px3 filtering should be used:
        return empty_filtering_result._replace(ranked=edges_ranked)
