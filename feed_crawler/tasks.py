from __future__ import absolute_import
import logging

import json
import random
import urllib2
from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError

from django.conf import settings
from django.utils import timezone

from targetshare import models
from targetshare.integration import facebook
from targetshare.tasks import db
from targetshare.models.dynamo.utils import to_epoch
from feed_crawler import utils

logger = get_task_logger(__name__)
rvn_logger = logging.getLogger('crow')
DELAY_INCREMENT = 300
S3_CONN = utils.S3Manager(
    aws_access_key_id=settings.AWS.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS.AWS_SECRET_ACCESS_KEY
)


@shared_task
def crawl_user(token, retry_count=0, max_retries=3):
    try:
        fresh_token = facebook.client.extend_token(
            token.fbid, token.appid, token.token
        )
    except IOError:
        # well, we tried
        rvn_logger.exception(
            'Failed to extend token for {}'.format(token.fbid)
        )
        if retry_count <= max_retries:
            return crawl_user(token, retry_count + 1)
        else:
            # Token is probably dead
            return
    else:
        fresh_token.save(overwrite=True)
        token = fresh_token

    try:
        edges = _bg_px4_crawl(token)
    except urllib2.HTTPError as exc:
        if 'invalid_token' in exc.headers.get('www-authenticate', ''):
            return # dead token
        raise
    fb_sync_maps = _get_sync_maps(edges, token)

    delay = 0
    for count, fbm in enumerate(fb_sync_maps, 1):
        if fbm.status == models.FBSyncMap.WAITING:
            initial_crawl.apply_async(
                args=[fbm],
                countdown=delay
            )
        elif fbm.status == models.FBSyncMap.COMPLETE:
            incremental_crawl.apply_async(
                args=[fbm],
                countdown=delay
            )

        delay += DELAY_INCREMENT if count % 100 == 0 else 0


def _bg_px4_crawl(token, retries=0, max_retries=3):
    ''' Very similar to the standard px4 task. The main difference is that
    this skips checking dynamo for data, as this is intended to constantly
    be feeding data into Dynamo. Also, it ships all saving tasks off to
    a different, feed_crawler specific queue as to not clog up the main,
    user facing, queues.
    '''
    try:
        user = facebook.client.get_user(token.fbid, token.token)
        stream = facebook.client.Stream.read(user, token.token)
        edges_unranked = stream.get_friend_edges(token.token)
    except IOError:
        retries += 1
        if retries > max_retries:
            raise
        else:
            return _bg_px4_crawl(token, retries)

    edges_ranked = edges_unranked.ranked(
        require_incoming=True,
        require_outgoing=False,
    )

    db.delayed_save.apply_async(
        args=[token],
        kwargs={'overwrite': True},
        queue='bg_delayed_save',
        routing_key='bg.delayed_save',
    )
    db.upsert.apply_async(
        args=[user],
        kwargs={'partial_save_queue': 'bg_partial_save'},
        queue='bg_upsert',
        routing_key='bg.upsert'
    )
    db.upsert.apply_async(
        args=[edge.secondary for edge in edges_ranked],
        kwargs={'partial_save_queue': 'bg_partial_save'},
        queue='bg_upsert',
        routing_key='bg.upsert',
    )
    db.bulk_create.apply_async(
        args=[tuple(edges_ranked.iter_interactions())],
        queue='bg_bulk_create',
        routing_key='bg.bulk.create',
    )
    db.upsert.apply_async(
        args=[
            models.dynamo.PostInteractionsSet(
                fbid=edge.secondary.fbid,
                postids=[post_interactions.postid
                         for post_interactions in edge.interactions],
            )
            for edge in edges_ranked
            if edge.interactions
        ],
        kwargs={'partial_save_queue': 'bg_partial_save'},
        queue='bg_upsert',
        routing_key='bg.upsert',
    )
    db.update_edges.apply_async(
        args=[edges_ranked],
        queue='bg_update_edges',
        routing_key='bg.update.edges'
    )

    return edges_ranked


def _get_sync_maps(edges, token):
    try:
        main_fbm = models.FBSyncMap.items.get_item(
            fbid_primary=token.fbid,
            fbid_secondary=token.fbid
        )
    except models.FBSyncMap.DoesNotExist:
        main_fbm = models.FBSyncMap.items.create(
            fbid_primary=token.fbid,
            fbid_secondary=token.fbid,
            token=token.token,
            back_filled=False,
            back_fill_epoch=0,
            incremental_epoch=0,
            status=models.FBSyncMap.WAITING,
            bucket=random.sample(settings.FEED_BUCKET_NAMES, 1)[0],
        )

    fb_sync_maps = [main_fbm]
    for edge in edges:
        try:
            fb_sync_maps.append(
                models.FBSyncMap.items.get_item(
                    fbid_primary=token.fbid,
                    fbid_secondary=edge.secondary.fbid,
                )
            )
        except models.FBSyncMap.DoesNotExist:
            fbm = models.FBSyncMap.items.create(
                fbid_primary=token.fbid,
                fbid_secondary=edge.secondary.fbid,
                token=token.token,
                back_filled=False,
                back_fill_epoch=0,
                incremental_epoch=0,
                status=models.FBSyncMap.WAITING,
                bucket=random.sample(settings.FEED_BUCKET_NAMES, 1)[0],
            )
            fb_sync_maps.append(fbm)

    return fb_sync_maps


@shared_task(bind=True, default_retry_delay=300, max_retries=5)
def initial_crawl(self, sync_map):
    logger.info('Starting initial crawl of {}'.format(sync_map.s3_key_name))
    sync_map.save_status(models.FBSyncMap.INITIAL_CRAWL)
    bucket = S3_CONN.get_or_create_bucket(sync_map.bucket)
    s3_key, created = bucket.get_or_create_key(sync_map.s3_key_name)
    past_epoch = to_epoch(timezone.now() - timedelta(days=365))
    now_epoch = to_epoch(timezone.now())
    try:
        data = facebook.client.urlload(
            'https://graph.facebook.com/{}/feed/'.format(sync_map.fbid_secondary), {
                'access_token': sync_map.token,
                'method': 'GET',
                'format': 'json',
                'suppress_http_code': 1,
                'limit': 5000,
                'since': past_epoch,
                'until': now_epoch,
            }, timeout=120
        )
    except (ValueError, IOError):
        try:
            self.retry()
        except MaxRetriesExceededError:
            sync_map.save_status(models.FBSyncMap.WAITING)
            return

    data['updated'] = now_epoch
    s3_key.set_contents_from_string(json.dumps(data))
    sync_map.back_fill_epoch = past_epoch
    sync_map.incremental_epoch = now_epoch
    sync_map.save_status(models.FBSyncMap.BACK_FILL)
    back_fill_crawl.apply_async(args=[sync_map], countdown=DELAY_INCREMENT)
    logger.info('Completed initial crawl of {}'.format(sync_map.s3_key_name))


@shared_task(bind=True, default_retry_delay=3600, max_retries=5)
def back_fill_crawl(self, sync_map):
    logger.info('Starting back fill crawl of {}'.format(sync_map.s3_key_name))
    bucket = S3_CONN.get_or_create_bucket(sync_map.bucket)
    s3_key, created = bucket.get_or_create_key(sync_map.s3_key_name)
    try:
        data = facebook.client.urlload(
            'https://graph.facebook.com/{}/feed/'.format(sync_map.fbid_secondary), {
                'access_token': sync_map.token,
                'method': 'GET',
                'format': 'json',
                'suppress_http_code': 1,
                'limit': 5000,
                'until': sync_map.back_fill_epoch,
            }, timeout=120
        )
    except (ValueError, IOError):
        try:
            self.retry()
        except MaxRetriesExceededError:
            # Hit a dead end. Given the retry delays and such, if we die here
            # we're likely, but not definitively at the end of the user's
            # feed
            rvn_logger.info(
                'Failed back fill crawl of {}'.format(sync_map.s3_key_name))

    next_url = data.get('paging', {}).get('next')
    if next_url and 'data' in data:
        result = facebook.client.exhaust_pagination(next_url)
        data['data'].extend(result)

    if 'data' in data:
        # If we don't have any data, the back fill likely failed. We'll go
        # ahead in that case and kick off the comment crawl, but not mark
        # this job as back filled so that we can give it another shot at some
        # later point
        full_data = json.loads(s3_key.get_contents_as_string())
        existing_data = full_data.setdefault('data', [])
        existing_data.extend(data['data'])
        full_data['updated'] = to_epoch(timezone.now())
        s3_key.set_contents_from_string(json.dumps(full_data))
        sync_map.back_filled = True
        sync_map.save()

    sync_map.save_status(models.FBSyncMap.COMMENT_CRAWL)
    crawl_comments_and_likes.apply_async(
        args=[sync_map], countdown=DELAY_INCREMENT
    )
    logger.info('Completed back fill crawl of {}'.format(sync_map.s3_key_name))


@shared_task(bind=True)
def crawl_comments_and_likes(self, sync_map):
    logger.info('Starting comment crawl of {}'.format(sync_map.s3_key_name))
    bucket = S3_CONN.get_or_create_bucket(sync_map.bucket)
    s3_key, created = bucket.get_or_create_key(sync_map.s3_key_name)
    feed = json.loads(s3_key.get_contents_as_string())
    if 'data' not in feed:
        # bogus/error'd out feed
        return

    for item in feed['data']:
        next_url = item.get('comments', {}).get('paging', {}).get('next')
        if next_url:
            result = facebook.client.exhaust_pagination(next_url)
            item['comments']['data'].extend(result)

        next_url = item.get('likes', {}).get('paging', {}).get('next')
        if next_url:
            result = facebook.client.exhaust_pagination(next_url)
            item['likes']['data'].extend(result)

    s3_key.set_contents_from_string(json.dumps(feed))
    sync_map.save_status(models.FBSyncMap.COMPLETE)
    logger.info('Completed comment crawl of {}'.format(sync_map.s3_key_name))


@shared_task(bind=True, default_retry_delay=300, max_retries=5)
def incremental_crawl(self, sync_map):
    logger.info('Starting incremental crawl of {}'.format(sync_map.s3_key_name))
    sync_map.save_status(models.FBSyncMap.INCREMENTAL)
    bucket = S3_CONN.get_or_create_bucket(sync_map.bucket)
    s3_key, created = bucket.get_or_create_key(sync_map.s3_key_name)
    try:
        data = facebook.client.urlload(
            'https://graph.facebook.com/{}/feed/'.format(sync_map.fbid_secondary), {
                'access_token': sync_map.token,
                'method': 'GET',
                'format': 'json',
                'suppress_http_code': 1,
                'limit': 5000,
                'since': sync_map.incremental_epoch,
            }, timeout=120
        )
    except (ValueError, IOError):
        try:
            self.retry()
        except MaxRetriesExceededError:
            # We'll get `em next time, boss.
            sync_map.save_status(models.FBSyncMap.COMPLETE)
            return

    next_url = data.get('paging', {}).get('next')
    if next_url:
        result = facebook.client.exhaust_pagination(next_url)
        data['data'].extend(result)

    full_data = json.loads(s3_key.get_contents_as_string())
    data['data'].extend(full_data['data'])
    data['updated'] = to_epoch(timezone.now())
    s3_key.set_contents_from_string(json.dumps(data))
    sync_map.incremental_epoch = to_epoch(timezone.now())
    sync_map.save()
    sync_map.save_status(models.FBSyncMap.COMPLETE)
    crawl_comments_and_likes.apply_async(
        args=[sync_map], countdown=DELAY_INCREMENT
    )
    logger.info('Completed incremental crawl of {}'.format(sync_map.s3_key_name))
