from __future__ import absolute_import

import itertools
import logging
from collections import namedtuple
from datetime import timedelta

import celery
import sentinels
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models.loading import get_model
from django.db.models import Q

from targetshare import utils
from targetshare.integration import facebook
from targetshare.models import datastructs, dynamo, relational
from targetshare.tasks import db


LOG = get_task_logger(__name__)
LOG_RVN = logging.getLogger('crow')


# Configuration constants #

# FIXME: Restore these values to their former glory after we handle
# null mutual friend counts from FB properly
DB_MIN_FRIEND_COUNT = 100
DB_FRIEND_THRESHOLD = 90 # percent

# The below width(s) of the proximity score spectrum from 1 to 0 will be
# partitioned during rank refinement:
# NOTE: We might want to review this threshold for various size networks
PX_REFINE_RANGE_WIDTH = 0.85

# The maximum number of (high-proximity) friends to bother rank-refining:
# NOTE: We might want to review this number, depending on how performant
# production is in ranking
PX_REFINE_MAX_COUNT = 500

# The maximum number of seconds that `proximity_rank_four` will wait for the
# `proximity_rank_three` task to complete, (when there are ranking key features
# but not px4 filter features, s.t. `px4_filter` defers to px3):
PX_REFINE_PX3_TIMEOUT = 3


# Return types #

FilteringResult = namedtuple('FilteringResult', [
    'ranked',
    'filtered',
    'cs_filter_id',
    'choice_set_slug',
    'campaign_id',
    'content_id',
])

empty_filtering_result = FilteringResult._make((None,) * 6)


# Reporting helpers #

NOVISIT = sentinels.Sentinel('NOVISIT') # like object() but [un]pickleable by workers


def record_visit_event(event_type, visit_id, visit_type='targetshare.Visit',
                       campaign_id=None, content_id=None):
    if visit_id is NOVISIT:
        LOG.debug("Skipping %r event record for non-visit", event_type)
        return
    (app, model_name) = visit_type.split('.')
    interaction = get_model(app, model_name).objects.get(pk=visit_id)
    interaction.events.create(
        campaign_id=campaign_id,
        client_content_id=content_id,
        event_type=event_type,
    )


def record_event(interaction, event_type, **kws):
    if interaction is NOVISIT:
        LOG.debug("Skipping %r event record for non-visit", event_type)
        return
    interaction.events.create(event_type=event_type, **kws)


def record_assignment(interaction, **kws):
    if interaction is NOVISIT:
        LOG.debug("Skipping assignment record for non-visit")
        return
    interaction.assignments.create(**kws)


def make_record_assignment(interaction, **kws):
    if interaction is NOVISIT:
        LOG.debug("Skipping assignment record for non-visit")
        return
    interaction.assignments.create_managed(**kws)


def get_recording_args(filtering_args):
    recording_args = {key: filtering_args[key] for key in ('visit_id',)}
    for key in ('visit_type', 'campaign_id', 'content_id'):
        try:
            value = filtering_args[key]
        except KeyError:
            pass
        else:
            recording_args[key] = value
    return recording_args


# Tasks #

@shared_task(default_retry_delay=1, max_retries=3, bind=True)
def proximity_rank_three(self, token, **filtering_args):
    """Build the px3 crawl-and-filter chain."""
    recording_args = get_recording_args(filtering_args)
    record_visit_event('px3_started', **recording_args)

    try:
        edges_ranked = px3_crawl(token)
    except IOError as exc:
        if self.request.retries == self.max_retries:
            record_visit_event('px3_failed', **recording_args)
        proximity_rank_three.retry(exc=exc)

    record_visit_event('px3_completed', **recording_args)
    return perform_filtering(edges_ranked, fbid=token.fbid, **filtering_args)


@shared_task
def px3_crawl(token):
    user = facebook.client.get_user(token.fbid, token.token)
    edges_unranked = facebook.client.get_friend_edges(user, token.token)
    return edges_unranked.ranked(
        require_incoming=False,
        require_outgoing=False,
    )


def perform_filtering(edges_ranked, campaign_id, content_id, fbid, visit_id, num_faces,
                      fallback_count=0, already_picked=None,
                      px_rank=3, visit_type='targetshare.Visit', cache_match=False):
    """Filter the given, ranked, Edges according to the configuration of the
    specified Campaign.

    """
    if fallback_count > settings.MAX_FALLBACK_COUNT:
        raise RuntimeError("Exceeded maximum fallback count")

    if visit_id is NOVISIT:
        interaction = NOVISIT
    else:
        (app, model_name) = visit_type.split('.')
        interaction = get_model(app, model_name).objects.get(pk=visit_id)

    if fallback_count == 0:
        record_event(
            interaction,
            campaign_id=campaign_id,
            client_content_id=content_id,
            content=px_rank,
            event_type='filtering_started',
        )

    client_content = relational.ClientContent.objects.get(content_id=content_id)
    campaign = relational.Campaign.objects.get(campaign_id=campaign_id)
    properties = campaign.campaignproperties.get()
    fallback_cascading = properties.fallback_is_cascading
    fallback_content_id = properties.fallback_content_id
    already_picked = already_picked or datastructs.TieredEdges()

    if properties.fallback_is_cascading and properties.fallback_campaign is None:
        LOG_RVN.warn("Campaign %s expects cascading fallback, but fails to specify fallback campaign.",
                     campaign_id)
        fallback_cascading = None

    # If fallback content empty, defer to current content
    if properties.fallback_content is None and properties.fallback_campaign is not None:
        fallback_content_id = content_id

    # For a cascading fallback, take any friends at all for
    # the current campaign to append to the list. Otherwise,
    # use the min_friends parameter as the threshold for errors.
    min_friends = 1 if fallback_cascading else properties.min_friends

    # Check if any friends should be excluded for this campaign & content
    # (Faces excluded from "campaign", not merely this fallback;
    # so, check against "root campaign")
    face_exclusions = relational.FaceExclusion.objects.filter(
        fbid=fbid,
        content=client_content,
        campaign__rootcampaign_properties__campaign=campaign,
    )
    exclude_friends = set(face_exclusions.values_list('friend_fbid', flat=True).iterator())
    exclude_friends.update(already_picked.secondary_ids) # don't re-add those already picked
    edges_eligible = [edge for edge in edges_ranked
                      if edge.secondary.fbid not in exclude_friends]

    # Assign filter experiments (and record) #

    # Apply global filter
    global_filter = campaign.campaignglobalfilters.random_assign()
    make_record_assignment(
        interaction,
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
    make_record_assignment(
        interaction,
        campaign=campaign,
        content=client_content,
        feature_row=choice_set,
        chosen_from_rows=campaign.campaignchoicesets,
    )
    (allow_generic, generic_slug) = campaign_choice_sets.values_list(
        'allow_generic', 'generic_url_slug'
    ).get(choice_set=choice_set)

    # Pick (and record) best choice set filter
    # NOTE: See above re: global filter.
    # Exclude ChoiceSetFilters written for super-ranked features:
    choice_set_filters = choice_set.choicesetfilters.exclude(
        filter__filterfeatures__feature_type__px_rank__gt=px_rank
    )
    if choice_set_filters:
        try:
            (best_csf, best_csf_edges) = choice_set_filters.choose_best_filter(
                edges_filtered,
                use_generic=allow_generic,
                min_friends=min_friends,
                cache_match=cache_match,
            )
        except relational.ChoiceSetFilter.TooFewFriendsError:
            LOG_RVN.debug("Too few friends found for user %s with campaign %s. "
                          "(Will check for fallback.)", fbid, campaign_id)
            best_csf_edges = None
    else:
        # No ChoiceSetFilters, on this ChoiceSet, (at this rank); skip filtering:
        (best_csf, best_csf_edges) = (None, edges_filtered)

    if best_csf_edges is not None:
        already_picked += datastructs.TieredEdges(
            edges=best_csf_edges,
            campaign_id=campaign_id,
            content_id=content_id,
            cs_filter_id=(best_csf.filter_id if best_csf else None),
            choice_set_slug=(best_csf.url_slug if best_csf else generic_slug),
        )
        if best_csf is None:
            template = "No ChoiceSetFilter applied ({}) for %s with campaign %s.".format(
                "used generic" if choice_set_filters else "none at rank"
            )
            LOG.debug(template, fbid, campaign_id)
            make_record_assignment(
                interaction,
                campaign=campaign,
                content=client_content,
                feature_row=None,
                random_assign=False,
                chosen_from_rows=choice_set.choicesetfilters,
                feature_type='generic choice set filter',
            )
        else:
            make_record_assignment(
                interaction,
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
        record_assignment(
            interaction,
            campaign=campaign,
            content=client_content,
            feature_type='cascading fallback campaign',
            feature_row=properties.fallback_campaign.pk,
            chosen_from_table='campaign_properties',
            chosen_from_rows=[properties.pk],
            random_assign=False,
        )
        record_assignment(
            interaction,
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
            if px_rank == 3:
                LOG_RVN.fatal("No fallback for %s with campaign %s. "
                              "(Will return error to user.)",
                              fbid, campaign_id)
            else:
                LOG_RVN.error("No fallback for %s with campaign %s.", fbid, campaign_id)

            record_event(
                interaction,
                campaign_id=campaign_id,
                client_content_id=content_id,
                content=px_rank,
                event_type='no_friends_error',
            )
            record_event(
                interaction,
                campaign_id=campaign_id,
                client_content_id=content_id,
                content=px_rank,
                event_type='filtering_completed',
            )
            return empty_filtering_result._replace(campaign_id=campaign_id,
                                                   content_id=content_id)

        # Record "fallback" assignments:
        record_assignment(
            interaction,
            campaign=campaign,
            content=client_content,
            feature_type='cascading fallback campaign',
            feature_row=properties.fallback_campaign.pk,
            chosen_from_table='campaign_properties',
            chosen_from_rows=[properties.pk],
            random_assign=False,
        )
        record_assignment(
            interaction,
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
        last_tier = already_picked[-1].copy()
        del last_tier['edges']
        result = FilteringResult(edges_ranked, already_picked, **last_tier)
        record_event(
            interaction,
            campaign_id=campaign_id,
            client_content_id=content_id,
            content=px_rank,
            event_type='filtering_completed',
        )
        return result


@shared_task(default_retry_delay=1, max_retries=3, bind=True)
def proximity_rank_four(self, token, freshness=None, **filtering_args):
    """Crawl, filter and rank a user's network to proximity level four, and
    persist the User, secondary Users, Token, PostInteractions and Edges to
    the database.

    (See `px4_crawl`, `px4_filter` and `px4_rank`.)

    """
    recording_args = get_recording_args(filtering_args)
    record_visit_event('px4_started', **recording_args)
    try:
        (stream, edges_ranked) = px4_crawl(token, freshness)
    except IOError as exc:
        if self.request.retries == self.max_retries:
            record_visit_event('px4_failed', **recording_args)
        proximity_rank_four.retry(exc=exc)

    record_visit_event('px4_completed', **recording_args)
    return px4_rank(px4_filter(stream, edges_ranked, fbid=token.fbid, **filtering_args))


def px4_crawl(token, freshness=None):
    """Retrieve the user's network from Facebook or from cache in Dynamo.

    If the user's network is under DB_MIN_FRIEND_COUNT friends, Facebook is always
    crawled; otherwise, if our database has at least DB_FRIEND_THRESHOLD percent of
    the network cached within settings.FRESHNESS days, then the database is used,
    instead.

    Data retrieved Facebook is subsequently cached in Dynamo.

    """
    # Retrieve user's network from Facebook or database
    user = facebook.client.get_user(token.fbid, token.token)

    friend_count = facebook.client.get_friend_count(token.fbid, token.token)
    if friend_count >= DB_MIN_FRIEND_COUNT:
        edges_unranked = datastructs.UserNetwork.get_friend_edges(
            user,
            require_incoming=True,
            require_outgoing=False,
            max_age=timedelta(days=(
                settings.FRESHNESS if freshness is None else freshness
            )),
        )
        if (
            not friend_count or
            100.0 * len(edges_unranked) / friend_count >= DB_FRIEND_THRESHOLD
        ):
            LOG.info('FBID %r: Has %r FB Friends, found %r in Dynamo; using Dynamo data.',
                     token.fbid, friend_count, len(edges_unranked))
            stream = None

        else:
            LOG.info('FBID %r: Has %r FB Friends, found %r in Dynamo; falling back to FB',
                     token.fbid, friend_count, len(edges_unranked))
            edges_unranked = None

    else:
        LOG.info('FBID %r: Has %r friends, hitting FB', token.fbid, friend_count)
        edges_unranked = None

    if edges_unranked is None:
        # We didn't use DDB or didn't like its results; retrieve from Facebook:
        stream = facebook.client.Stream.read(user, token.token)
        edges_unranked = stream.get_friend_edges(token.token)

    # Rank friends by interactional proximity:
    edges_ranked = edges_unranked.ranked(
        require_incoming=True,
        require_outgoing=False,
    )

    # Persist novel data
    db.upsert.delay(user)

    if stream is not None:
        # Enqueue tasks to persist data retrieved from Facebook

        # Secondary Users:
        db.upsert.delay([edge.secondary for edge in edges_ranked])

        # PostInteractions:
        db.bulk_create.delay(tuple(edges_ranked.iter_interactions()))
        db.upsert.delay([
            dynamo.PostInteractionsSet(
                fbid=edge.secondary.fbid,
                postids=[post_interactions.postid
                         for post_interactions in edge.interactions],
            )
            for edge in edges_ranked
            if edge.interactions
        ])

        # Edges:
        db.update_edges.delay(edges_ranked)

    return (stream, edges_ranked)


def _fallback_campaign(campaign_id):
    """Return from the database the primary key of the fallback campaign
    (if any) of the campaign with the given primary key (`campaign_id`).

    """
    return (relational.CampaignProperties.objects
        .values_list('fallback_campaign', flat=True)
        .get(campaign_id=campaign_id))


def px4_filter(stream, edges_ranked, campaign_id, content_id, fbid, visit_id, num_faces,
               px3_task_id=None, visit_type='targetshare.Visit', cache_match=False, force=False):
    """Apply px4 filtering to the result of `px4_crawl`.

    Filtering is achieved through `perform_filtering`, and so edges are filtered
    and campaign fallbacks are applied; however, if no px4-specific filters are
    defined for the campaign nor its fallbacks, the filtered set and final campaign
    is instead determined from the asynchronous results of `proximity_rank_three`.

    Note: This method inspects the campaign and its fallbacks for filters *and*
    ranking keys requiring a topics feature, and prepopulates this User property
    from the UserNetwork (and, if available, Stream) data taken from `px4_crawl`,
    to avoid the overhead of implicit database calls per User.

    """
    # Follow campaign's fallback chain:
    campaigns = [campaign_id]
    fallback_id = _fallback_campaign(campaign_id)
    while fallback_id is not None:
        campaigns.append(fallback_id)
        fallback_id = _fallback_campaign(fallback_id)

    # Build query to check for existence of relevant (px4) filter features:
    campaign_global = Q(filter__campaignglobalfilters__campaign__in=campaigns)
    campaign_choiceset = Q(
        filter__choicesetfilters__choice_set__campaignchoicesets__campaign__in=campaigns)
    px4_filter_features = relational.FilterFeature.objects.for_datetime().filter(
        (campaign_global | campaign_choiceset),
        feature_type__px_rank__gte=4,
    )
    # ..and ranking features:
    ranking_features = relational.RankingKeyFeature.objects.filter(
        ranking_key__campaignrankingkeys__campaign__in=campaigns,
    ).for_datetime()

    # Eagerly retrieve and/or compute relevant PostTopics:
    topics_filter_features = px4_filter_features.filter(
        feature_type__code=relational.FilterFeatureType.TOPICS,
    ).values_list('feature', flat=True).distinct()
    topics_ranking_features = ranking_features.filter(
        feature_type__code=relational.RankingFeatureType.TOPICS,
    ).values_list('feature', flat=True).distinct()
    topic_parser = relational.FilterFeature.Expression.ALL['topics']
    topics_features = {
        topic_parser.search(feature).group(1)
        for feature in itertools.chain(
            topics_filter_features,
            topics_ranking_features,
        )
    }
    if topics_features:
        # Bulk-retrieve topics of all posts with which network has interacted:
        (post_topics, missing_posts) = dynamo.PostTopics.items.batch_get_best(
            (post_interactions.postid for post_interactions in edges_ranked.iter_interactions()),
            # If we have no stream, settle for existing quick-dirty classifications;
            # (otherwise, we'll ensure appropriate quick-dirty classification of posts below):
            dynamo.PostTopics.CLASSIFIERS if stream is None else (dynamo.PostTopics.BG_CLASSIFIER,)
        )
        if missing_posts and stream is not None:
            # Attempt to fill in missing PostTopics from Stream Posts:
            qd_post_topics = [
                dynamo.PostTopics.classify(
                    post.post_id,
                    post.message,
                    *topics_features
                )
                for post in stream
                if post.message and post.post_id in missing_posts
            ]
            db.upsert.delay(qd_post_topics)
            post_topics += qd_post_topics

        # Pre-cache User.topics
        # NOTE: If network was read from FB, calculations will be limited to
        # contents of primary's posts (currently)
        edges_ranked.precache_topics_feature(post_topics)

    ## px4 filtering ##

    filtering_result = None

    # (No need for `exists()` query `if topics_filter_features`):
    if force or topics_filter_features or px4_filter_features.exists():
        try:
            filtering_result = perform_filtering(
                edges_ranked, campaign_id, content_id, fbid, visit_id, num_faces,
                px_rank=4, visit_type=visit_type, cache_match=cache_match
            )
        except Exception:
            LOG_RVN.exception("px4 filtering failure")
    elif px3_task_id is not None:
        # Retrieve px3 result:
        px3_task = celery.current_app.AsyncResult(px3_task_id)

        px3_result = None
        if ranking_features.exists() and not px3_task.ready():
            # Wait on px3 task for a (limited) time (avoid deadlocks):
            try:
                px3_result = px3_task.get(
                    timeout=PX_REFINE_PX3_TIMEOUT,
                    propagate=False,
                    interval=0.2,
                )
            except Exception:
                # Timeout or communication error
                pass

        if px3_task.successful():
            px3_result = px3_result or px3_task.result
            if px3_result and px3_result.filtered:
                filtering_result = px3_result._replace(
                    ranked=edges_ranked,
                    filtered=px3_result.filtered.reranked(edges_ranked),
                )

    if filtering_result and filtering_result.filtered:
        return filtering_result

    # Can't continue with rank refinement.
    # Use empty result to indicate px3 filtering should be used:
    return empty_filtering_result._replace(ranked=edges_ranked)


def px4_rank(filtering_result):
    """Apply custom (not proximity-based) ranking to the results of `px4_filter`."""
    args = (filtering_result.ranked,
            filtering_result.filtered,
            filtering_result.campaign_id)

    if not all(args):
        # Nothing to rank:
        return filtering_result

    (edges, filtered, campaign_id) = args

    try:
        campaign_ranking_key = (relational.CampaignRankingKey.objects
                                .for_datetime().get(campaign_id=campaign_id))
    except relational.CampaignRankingKey.DoesNotExist:
        # No active rank refinements to apply
        return filtering_result
    except relational.CampaignRankingKey.MultipleObjectsReturned:
        # Multiple ranking keys not currently supported.
        # (Could use rand_cdf/random_assign in the future.)
        # (Note, to apply multiple sorting keys, a RankingKey may have multiple
        # RankingKeyFeatures.)
        LOG.exception("Campaign %s has multiple active ranking keys; "
                      "will not refine rank.", campaign_id)
        return filtering_result

    # Only bother ranking the first PX_REFINE_MAX_COUNT friends:
    (edges_rerank, edges_tail) = (edges[:PX_REFINE_MAX_COUNT],
                                  edges[PX_REFINE_MAX_COUNT:])

    # ...and partition edges s.t. those with px score above threshold
    # (1 - PX_REFINE_RANGE_WIDTH) remain separate from those below:
    edges_partitioned = utils.partition_edges(edges_rerank, range_width=PX_REFINE_RANGE_WIDTH)

    keys = campaign_ranking_key.ranking_key.rankingkeyfeatures.for_datetime()
    edges_reranked = itertools.chain.from_iterable(
        keys.sorted_edges(partition)
        for (_lower_bound, partition) in edges_partitioned
    )
    edges_ranked = datastructs.UserNetwork(
        itertools.chain(edges_reranked, edges_tail)
    )

    return filtering_result._replace(
        ranked=edges_ranked,
        filtered=filtered.reranked(edges_ranked),
    )
