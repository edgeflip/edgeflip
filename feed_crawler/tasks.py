from __future__ import absolute_import

import logging
import random
import urllib2
from datetime import datetime, timedelta
from httplib import HTTPException

from boto.dynamodb2.exceptions import ConditionalCheckFailedException
from celery import shared_task
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError

from django.conf import settings
from django.utils import timezone
from faraday.utils import epoch

from targetshare import models
from targetshare.integration import facebook
from targetshare.tasks import db
from feed_crawler import s3_feed

logger = get_task_logger(__name__)
rvn_logger = logging.getLogger('crow')
DELAY_INCREMENT = 300
S3_CONN = s3_feed.S3Manager(
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)
UTCMIN = datetime.min.replace(tzinfo=epoch.UTC)


def expires_safe(token):
    return token.get('expires', UTCMIN)


@shared_task(max_retries=6)
def crawl_user(fbid, retry_delay=0):
    """Enqueue crawl tasks for the user (`fbid`) and the users of his/her network."""
    # Find a valid token for the user #
    tokens = models.Token.items.query(fbid__eq=fbid)
    # Iterate over user's tokens, starting with most recent:
    for token in sorted(tokens, key=expires_safe, reverse=True):
        # We expect values of "expires" to be optimistic, meaning we trust dates
        # in the past, but must confirm dates in the future.
        # (We sometimes set field optimistically; and, user can invalidate our
        # token, throwing its actual expires to 0.)

        if not token.expires or token.expires <= epoch.utcnow():
            return # This, and any remaining, invalid

        # Confirm token expiration (and validity)
        try:
            debug_result = facebook.client.debug_token(token.appid, token.token)
            debug_data = debug_result['data']
            token_valid = debug_data['is_valid']
            token_expires = debug_data['expires_at']
        except (KeyError, IOError, RuntimeError) as exc:
            # Facebook is being difficult; retry later (with increasing wait):
            # (We would use self.request.retries rather than define
            # retry_delay; but, we don't want to increase the countdown for
            # *all* retries.)
            crawl_user.retry((fbid, 2 * (retry_delay + 60)), {},
                             countdown=retry_delay, exc=exc)

        # Update token, if needed; but, restart if another process has changed
        # the token (meaning it may now refer to new value):
        token.expires = token_expires
        try:
            token.partial_save()
        except ConditionalCheckFailedException as exc:
            # Token has changed since we loaded it; retry:
            crawl_user.retry((fbid, retry_delay), {}, countdown=0, exc=exc)

        if token_valid and token.expires > epoch.utcnow():
            # We have our token, no lie!
            break
    else:
        return # All tokens were invalid (and liars)

    try:
        edges = _bg_px4_crawl(token)
    except urllib2.HTTPError as exc:
        if 'invalid_token' in exc.headers.get('www-authenticate', ''):
            return # dead token
        raise

    fb_sync_maps = _get_sync_maps(edges, token)

    delay = 0
    for (count, fbm) in enumerate(fb_sync_maps, 1):
        if fbm.status == models.FBSyncMap.WAITING:
            fbm.save_status(models.FBSyncMap.QUEUED)
            initial_crawl.apply_async(
                args=[fbm.fbid_primary, fbm.fbid_secondary],
                countdown=delay
            )
        elif fbm.status == models.FBSyncMap.COMPLETE:
            fbm.save_status(models.FBSyncMap.QUEUED)
            incremental_crawl.apply_async(
                args=[fbm.fbid_primary, fbm.fbid_secondary],
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
def initial_crawl(self, primary, secondary):
    sync_map = models.FBSyncMap.items.get_item(
        fbid_primary=primary, fbid_secondary=secondary)
    logger.info('Starting initial crawl of %s', sync_map.s3_key_name)
    sync_map.save_status(models.FBSyncMap.INITIAL_CRAWL)
    past_epoch = epoch.from_date(timezone.now() - timedelta(days=365))
    now_epoch = epoch.from_date(timezone.now())
    try:
        bucket = S3_CONN.get_or_create_bucket(sync_map.bucket)
        s3_key, _ = bucket.get_or_create_key(sync_map.s3_key_name)
        s3_key.retrieve_fb_feed(
            sync_map.fbid_secondary, sync_map.token, past_epoch, now_epoch
        )
    except (facebook.client.OAuthException):
        rvn_logger.info('Failed initial crawl due to expired token for %s',
                        sync_map.s3_key_name)
        return
    except (ValueError, IOError, HTTPException):
        try:
            self.retry()
        except MaxRetriesExceededError:
            sync_map.save_status(models.FBSyncMap.WAITING)
            return

    s3_key.data['updated'] = now_epoch
    try:
        s3_key.save_to_s3()
    except HTTPException as exc:
        self.retry(exc=exc)

    sync_map.back_fill_epoch = past_epoch
    sync_map.incremental_epoch = now_epoch
    sync_map.save_status(models.FBSyncMap.PAGE_LIKES)
    retrieve_page_likes.apply_async(
        args=[sync_map.fbid_primary, sync_map.fbid_secondary],
        countdown=DELAY_INCREMENT
    )
    logger.info('Completed initial crawl of %s', sync_map.s3_key_name)


@shared_task(bind=True, max_retries=5)
def retrieve_page_likes(self, primary, secondary):
    sync_map = models.FBSyncMap.items.get_item(
        fbid_primary=primary, fbid_secondary=secondary
    )
    logger.info('Starting page like retrieval of %s', sync_map.s3_key_name)
    try:
        bucket = S3_CONN.get_or_create_bucket(sync_map.bucket)
        s3_key, _ = bucket.get_or_create_key(sync_map.s3_key_name)
        likes = s3_key.retrieve_page_likes(sync_map.fbid_secondary, sync_map.token)
    except (facebook.client.OAuthException):
        rvn_logger.info('Failed page like retrieval due to expired token for %s',
                        sync_map.s3_key_name)
        return
    except (IOError, HTTPException):
        try:
            self.retry()
        except MaxRetriesExceededError:
            rvn_logger.info('Failed page like retrieval of %s', sync_map.s3_key_name, exc_info=True)
    else:
        s3_key.set_s3_likes(likes)

    sync_map.save_status(models.FBSyncMap.BACK_FILL)
    back_fill_crawl.apply_async(
        args=[sync_map.fbid_primary, sync_map.fbid_secondary],
        countdown=DELAY_INCREMENT
    )
    logger.info('Completed page like retrieval of %s', sync_map.s3_key_name)


@shared_task(bind=True, default_retry_delay=3600, max_retries=5)
def back_fill_crawl(self, primary, secondary):
    sync_map = models.FBSyncMap.items.get_item(
        fbid_primary=primary, fbid_secondary=secondary)
    logger.info('Starting back fill crawl of %s', sync_map.s3_key_name)
    try:
        bucket = S3_CONN.get_or_create_bucket(sync_map.bucket)
        s3_key, _ = bucket.get_or_create_key(sync_map.s3_key_name)
        s3_key.retrieve_fb_feed(
            sync_map.fbid_secondary, sync_map.token,
            0, sync_map.back_fill_epoch
        )
    except (facebook.client.OAuthException):
        rvn_logger.info('Failed back fill crawl due to expired token for %s',
                        sync_map.s3_key_name)
        return
    except (ValueError, IOError):
        try:
            self.retry()
        except MaxRetriesExceededError:
            # Hit a dead end. Given the retry delays and such, if we die here
            # we're likely, but not definitively at the end of the user's
            # feed
            rvn_logger.info('Failed back fill crawl of %s', sync_map.s3_key_name)
    else:
        try:
            s3_key.crawl_pagination()
        except (facebook.client.OAuthException):
            rvn_logger.info('Failed back fill crawl due to expired token for %s',
                            sync_map.s3_key_name)
            return
        if 'data' in s3_key.data:
            # If we don't have any data, the back fill likely failed. We'll go
            # ahead in that case and kick off the comment crawl, but not mark
            # this job as back filled so that we can give it another shot at some
            # later point
            try:
                s3_key.extend_s3_data()
            except HTTPException as exc:
                self.retry(exc=exc)
            sync_map.back_filled = True
            sync_map.save()

    sync_map.save_status(models.FBSyncMap.COMMENT_CRAWL)
    crawl_comments_and_likes.apply_async(
        args=[sync_map.fbid_primary, sync_map.fbid_secondary],
        countdown=DELAY_INCREMENT
    )
    logger.info('Completed back fill crawl of %s', sync_map.s3_key_name)


@shared_task(bind=True)
def crawl_comments_and_likes(self, primary, secondary):
    sync_map = models.FBSyncMap.items.get_item(
        fbid_primary=primary, fbid_secondary=secondary)
    logger.info('Starting comment crawl of %s', sync_map.s3_key_name)
    try:
        bucket = S3_CONN.get_or_create_bucket(sync_map.bucket)
        s3_key, _ = bucket.get_or_create_key(sync_map.s3_key_name)
        s3_key.populate_from_s3()
    except HTTPException as exc:
        self.retry(exc=exc)

    if 'data' not in s3_key.data:
        # bogus/error'd out feed
        return

    try:
        for item in s3_key.data['data']:
            next_url = item.get('comments', {}).get('paging', {}).get('next')
            if next_url:
                result = facebook.client.exhaust_pagination(next_url)
                item['comments']['data'].extend(result)

            next_url = item.get('likes', {}).get('paging', {}).get('next')
            if next_url:
                result = facebook.client.exhaust_pagination(next_url)
                item['likes']['data'].extend(result)
    except (facebook.client.OAuthException):
        rvn_logger.info('Failed comment crawl due to expired token for %s',
                        sync_map.s3_key_name)
        return
    try:
        s3_key.save_to_s3()
    except HTTPException as exc:
        self.retry(exc=exc)

    sync_map.save_status(models.FBSyncMap.COMPLETE)
    logger.info('Completed comment crawl of %s', sync_map.s3_key_name)


@shared_task(bind=True, default_retry_delay=300, max_retries=5)
def incremental_crawl(self, primary, secondary):
    sync_map = models.FBSyncMap.items.get_item(
        fbid_primary=primary, fbid_secondary=secondary)
    logger.info('Starting incremental crawl of %s', sync_map.s3_key_name)
    sync_map.save_status(models.FBSyncMap.INCREMENTAL)
    try:
        bucket = S3_CONN.get_or_create_bucket(sync_map.bucket)
        s3_key, created = bucket.get_or_create_key(sync_map.s3_key_name)
        s3_key.retrieve_fb_feed(
            sync_map.fbid_secondary, sync_map.token,
            sync_map.incremental_epoch, epoch.from_date(timezone.now())
        )
    except (facebook.client.OAuthException):
        rvn_logger.info('Failed incremental crawl due to expired token for %s',
                        sync_map.s3_key_name)
        return
    except (ValueError, IOError):
        try:
            self.retry()
        except MaxRetriesExceededError:
            # We'll get `em next time, boss.
            rvn_logger.info('Failed incremental crawl of %s', sync_map.s3_key_name)
    else:
        try:
            s3_key.crawl_pagination()
        except (facebook.client.OAuthException):
            rvn_logger.info('Failed incremental crawl due to expired token for %s',
                            sync_map.s3_key_name)
            return

        if 'data' in s3_key.data:
            # If we have data, let's save it. If not, let's kick this guy over
            # to crawl_comments_and_likes. We'll get that incremental data later
            try:
                s3_key.extend_s3_data(False)
            except HTTPException as exc:
                self.retry(exc=exc)
            sync_map.incremental_epoch = epoch.from_date(timezone.now())
            sync_map.save()
            crawl_comments_and_likes.apply_async(
                args=[sync_map.fbid_primary, sync_map.fbid_secondary],
                countdown=DELAY_INCREMENT
            )

    sync_map.save_status(models.FBSyncMap.COMPLETE)
    logger.info('Completed incremental crawl of %s', sync_map.s3_key_name)
