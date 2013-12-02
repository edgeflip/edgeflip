from __future__ import absolute_import

import json
import random
import urllib
import time

import celery
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from targetshare import models
from targetshare.integration import facebook
from targetshare.tasks import ranking
from targetshare.models.dynamo.utils import to_epoch
from feed_crawler import utils

logger = get_task_logger(__name__)
MIN_FRIEND_COUNT = 100
FRIEND_THRESHOLD_PERCENT = 90


def crawl_user(token):
    task = ranking.proximity_rank_four.apply_async(
        args=[False, token.fbid, token],
        routing_key='bg.px4',
        link=create_sync_task.s(token=token)
    )
    return task


@celery.task(default_retry_delay=1, max_retries=3)
def create_sync_task(edges, token):
    if not edges:
        return

    try:
        sync_task = models.FBSyncTask.items.get_item(fbid=token.fbid)
    except models.FBSyncTask.DoesNotExist:
        pass
    else:
        if sync_task.is_processing:
            logger.info('Have an existing task for {}. Moving on.'.format(
                token.fbid))
            return

    sync_task = models.FBSyncTask(
        fbid=token.fbid,
        token=token.token,
        status=models.FBSyncTask.WAITING,
    )
    fbids_to_crawl = [token.fbid] + [edge.secondary.fbid for edge in edges]
    sync_task.fbids_to_crawl = fbids_to_crawl
    sync_task.save()
    process_sync_task.delay(token.fbid)


@celery.task(default_retry_delay=300, max_retries=3)
def process_sync_task(primary_fbid):
    sync_task = models.FBSyncTask.items.get_item(fbid=primary_fbid)
    sync_task.status = sync_task.IN_PROCESS
    sync_task.save(overwrite=True)
    s3_conn = utils.S3Manager()

    logger.info('Preparing to crawl {} fbids'.format(
        len(sync_task.fbids_to_crawl)))
    fbids_to_crawl = set(sync_task.fbids_to_crawl)
    for fbid in fbids_to_crawl:
        bucket = s3_conn.get_or_create_bucket('{}{}'.format(
            settings.FEED_BUCKET_PREFIX,
            random.randrange(0, settings.FEED_MAX_BUCKETS)
        ))
        logger.info('Processing {}_{}'.format(sync_task.fbid, fbid))
        s3_key, created = bucket.get_or_create_key('{}_{}'.format(
            sync_task.fbid,
            fbid
        ))

        if not created:
            logger.info('Found existing S3 Key for {}_{}'.format(
                sync_task.fbid, fbid))
            data = json.loads(s3_key.get_contents_as_string())
            next_url = 'https://graph.facebook.com/{}/feed?{}'.format(
                fbid, urllib.urlencode({
                    'until': data['updated'],
                    'limit': 1000,
                    'method': 'GET',
                    'format': 'json',
                    'suppress_http_code': 1,
                })
            )
        else:
            logger.info('No existing S3 Key for {}_{}'.format(
                sync_task.fbid, fbid))
            try:
                data = facebook.client.urlload(
                    'https://graph.facebook.com/{}/feed/'.format(fbid), {
                        'access_token': sync_task.token,
                        'method': 'GET',
                        'format': 'json',
                        'suppress_http_code': 1,
                        'limit': 1000,
                        'until': to_epoch(timezone.now()),
                    }, timeout_override=120
                )
                if not data.get('data'):
                    logger.info('No feed information for {}'.format(
                        fbid))
                    return

                next_url = data.get('paging', {}).get('next')
            except (ValueError, IOError) as exc:
                logger.exception(
                    'Failed to process initial url for {}_{}'.format(
                        sync_task.fbid, fbid)
                )
                try:
                    process_sync_task.retry(exc=exc)
                except (ValueError, IOError):
                    logger.exception(
                        'Completely failed to process {}_{}'.format(
                            sync_task.fbid, fbid)
                    )
                    sync_task.status = sync_task.FAILED
                    sync_task.save(overwrite=True)

        retry_count = 0
        while next_url:
            logger.info('Crawling {} for {}_{}'.format(
                next_url, sync_task.fbid, fbid))
            try:
                paginated_data = facebook.client.urlload(
                    next_url, timeout_override=120)
            except (ValueError, IOError) as exc:
                logger.exception(
                    'Failed to grab next page of data for {}_{}'.format(
                        sync_task.fbid, fbid)
                )
                retry_count += 1
                if retry_count > 3:
                    break
                else:
                    continue
                time.sleep(5)

            else:
                if paginated_data.get('data'):
                    data['data'].extend(paginated_data['data'])
                    next_url = paginated_data.get('paging', {}).get('next')
                else:
                    next_url = None

        data['updated'] = to_epoch(timezone.now())
        s3_key.set_contents_from_string(json.dumps(data))
        sync_task.fbids_to_crawl.remove(fbid)
        sync_task.save(overwrite=True)
        logger.info('Completed {}_{}'.format(sync_task.fbid, fbid))

    sync_task.status = sync_task.COMPLETED
    sync_task.save(overwrite=True)
