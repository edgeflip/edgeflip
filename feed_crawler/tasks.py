from __future__ import absolute_import

import json
import random
import urllib
from datetime import timedelta

import boto
import celery
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from targetshare import models
from targetshare.integration import facebook
from targetshare.tasks import ranking
from targetshare.models.dynamo.utils import to_epoch

logger = get_task_logger(__name__)
MIN_FRIEND_COUNT = 100
FRIEND_THRESHOLD_PERCENT = 90


def crawl_user(token):
    task = ranking.proximity_rank_four.apply_async(
        args=[False, token.fbid, token],
        routing_key='bg.px4',
        link=crawl_user_feeds.s(token=token)
    )
    return task


@celery.task(default_retry_delay=1, max_retries=3)
def crawl_user_feeds(edges, token):
    if not edges:
        return

    primary_user = edges[0].primary
    freshness_limit = timezone.now() - timedelta(days=settings.FEED_AGE_LIMIT)

    try:
        prim_fbm = models.FeedBucketMap.items.get_item(
            fbid_source=primary_user.fbid,
            fbid_target=primary_user.fbid,
        )
    except models.FeedBucketMap.DoesNotExist:
        bucket = '{}{}'.format(
            settings.FEED_BUCKET_PREFIX,
            random.randrange(0, settings.FEED_MAX_BUCKETS)
        )
        prim_fbm = models.FeedBucketMap(
            fbid_source=primary_user.fbid,
            fbid_target=primary_user.fbid,
            bucket=bucket
        )

    prim_fbm.token = token.token
    prim_fbm.save()
    store_user_feed.delay(prim_fbm)

    countdown_time = 0
    edge_count = 0
    edges_dict = {}
    for edge in edges:
        edges_dict[edge.secondary.id] = 0

    del edges
    for secondary_fbid, failure_count in edges_dict.iteritems():
        try:
            fbm = models.FeedBucketMap.items.get_item(
                fbid_source=primary_user.fbid,
                fbid_target=secondary_fbid,
            )
        except models.FeedBucketMap.DoesNotExist:
            bucket = '{}{}'.format(
                settings.FEED_BUCKET_PREFIX,
                random.randrange(0, settings.FEED_MAX_BUCKETS)
            )
            fbm = models.FeedBucketMap(
                fbid_source=primary_user.fbid,
                fbid_target=secondary_fbid,
                bucket=bucket,
            )
        else:
            # Got an existing person, lets check the freshness
            if fbm.updated > freshness_limit:
                continue

        fbm.token = token.token
        fbm.save()
        # Need to find a way to continue processing this loop until its
        # exhausted
        store_user_feed(fbm)


@celery.task(default_retry_delay=300, max_retries=3)
def store_user_feed(feed_bucket_map):
    s3_conn = boto.s3.connect_to_region('us-east-1')
    try:
        bucket = s3_conn.get_bucket(feed_bucket_map.bucket)
    except boto.exception.S3ResponseError:
        try:
            bucket = s3_conn.create_bucket(feed_bucket_map.bucket)
        except boto.exception.S3ResponseError as exc:
            store_user_feed.retry(exc=exc)

    s3_key = bucket.get_key('{}_{}'.format(
        feed_bucket_map.fbid_source,
        feed_bucket_map.fbid_target
    ))
    if not s3_key:
        s3_key = bucket.new_key('{}_{}'.format(
            feed_bucket_map.fbid_source,
            feed_bucket_map.fbid_target
        ))

    if s3_key.size:
        data = json.loads(s3_key.get_contents_as_string())
        next_url = 'https://graph.facebook.com/{}/feed?{}'.format(
            feed_bucket_map.fbid_target, urllib.urlencode({
                'until': data['updated'],
                'limit': 1000,
                'method': 'GET',
                'format': 'json',
                'suppress_http_code': 1,
            })
        )
    else:
        try:
            data = facebook.client.urlload(
                'https://graph.facebook.com/{}/feed/'.format(feed_bucket_map.fbid_target), {
                    'access_token': feed_bucket_map.token,
                    'method': 'GET',
                    'format': 'json',
                    'suppress_http_code': 1,
                    'limit': 1000,
                    'until': to_epoch(timezone.now()),
                }, timeout_override=120
            )
            data['updated'] = to_epoch(timezone.now())
            if not data.get('data'):
                logger.info('No feed information for {}'.format(
                    feed_bucket_map.fbid_target))
                return

            next_url = data.get('paging', {}).get('next')
        except IOError as exc:
            raise #store_user_feed.retry(exc=exc)

    while next_url:
        try:
            paginated_data = facebook.client.urlload(next_url, timeout_override=120)
        except IOError as exc:
            #logger.exception('Failed to grab next page of data for {}'.format(
            #    feed_bucket_map.fbid_target))
            #store_user_feed.retry(exc=exc)
            raise
        else:
            if paginated_data.get('data'):
                data['data'].extend(paginated_data['data'])
                next_url = data.get('paging', {}).get('next')
            else:
                next_url = None

    s3_key.set_contents_from_string(json.dumps(data))
