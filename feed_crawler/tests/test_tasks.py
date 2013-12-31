import os
import json
import urllib2

from mock import Mock, patch

from django.utils import timezone

from targetshare.tests import EdgeFlipTestCase, patch_facebook
from targetshare.tasks.ranking import px3_crawl
from targetshare import models

from feed_crawler import tasks, utils

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


class TestFeedCrawlerTasks(EdgeFlipTestCase):

    def setUp(self):
        super(TestFeedCrawlerTasks, self).setUp()
        expires = timezone.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.token = models.dynamo.Token(fbid=1, appid=1, token='1', expires=expires)

    @patch_facebook
    def test_bg_px4_crawl(self):
        self.assertFalse(models.dynamo.IncomingEdge.items.scan(limit=1))

        ranked_edges = tasks.bg_px4_crawl(self.token)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)
        assert all(x.incoming.post_likes is not None for x in ranked_edges)

        self.assertTrue(models.dynamo.IncomingEdge.items.scan(limit=1))
        # We know we have a call to get the user and the friend count at the
        # very least. However, hitting FB should spawn many more hits to FB
        self.assertGreater(urllib2.urlopen.call_count, 2)

    @patch_facebook
    @patch('feed_crawler.tasks.process_sync_task')
    def test_create_sync_task(self, sync_mock):
        ''' Should create a FBTaskSync object and place a process_sync_task
        job on the queue
        '''
        edges = px3_crawl(self.token)
        tasks.create_sync_task(edges, self.token)
        fbt = models.FBSyncTask.items.get_item(fbid=1)
        self.assertEqual(fbt.status, 'waiting')
        self.assertEqual(fbt.token, self.token.token)
        self.assertTrue(sync_mock.delay.called)

    @patch_facebook
    @patch('feed_crawler.tasks.process_sync_task')
    def test_create_sync_task_existing_task(self, sync_mock):
        ''' Should recognize an existing FBTaskSync object and do nothing '''
        fbt = models.FBSyncTask(
            fbid=1,
            token='test',
            status=models.FBSyncTask.WAITING,
            fbids_to_crawl={1, 2, 3}
        )
        fbt.save()
        edges = px3_crawl(self.token)
        tasks.create_sync_task(edges, self.token)
        self.assertFalse(sync_mock.delay.called)

    @patch_facebook
    @patch('feed_crawler.utils.S3Manager.get_bucket')
    @patch('feed_crawler.utils.BucketManager.get_key')
    @patch('feed_crawler.utils.BucketManager.new_key')
    def test_process_sync_task_new_key(self, new_bucket_mock, bucket_mock, conn_mock):
        new_key = Mock()
        new_bucket_mock.return_value = new_key
        bucket_mock.return_value = None
        conn_mock.return_value = utils.BucketManager()
        fbt = models.FBSyncTask(
            fbid=1,
            token='test',
            status=models.FBSyncTask.WAITING,
            fbids_to_crawl={1}
        )
        fbt.save()
        tasks.process_sync_task(fbt.fbid)
        self.assertTrue(new_key.set_contents_from_string.called)
        with self.assertRaises(models.FBSyncTask.DoesNotExist):
            models.FBSyncTask.items.get_item(fbid=1)

    @patch_facebook
    @patch('feed_crawler.utils.S3Manager.get_bucket')
    @patch('feed_crawler.utils.BucketManager.get_key')
    def test_process_sync_task_existing_key(self, bucket_mock, conn_mock):
        existing_key = Mock()
        existing_key.get_contents_as_string.return_value = '{"updated": 1, "data": [{"test": "testing"}]}'
        bucket_mock.return_value = existing_key
        conn_mock.return_value = utils.BucketManager()
        fbt = models.FBSyncTask(
            fbid=1,
            token='test',
            status=models.FBSyncTask.WAITING,
            fbids_to_crawl={1}
        )
        fbt.save()
        tasks.process_sync_task(fbt.fbid)
        self.assertTrue(existing_key.get_contents_as_string.called)
        self.assertTrue(existing_key.set_contents_from_string.called)
        with self.assertRaises(models.FBSyncTask.DoesNotExist):
            models.FBSyncTask.items.get_item(fbid=1)

    @patch('targetshare.integration.facebook.client.urlload')
    def test_crawl_comments_and_likes(self, fb_mock):
        fb_mock.side_effect = [
            {"data": [
                {
                    "id": "10151910724132946_11479371",
                    "from": {
                        "name": "Alex Tevlin",
                        "id": "794333711"
                    },
                    "message": "Should've stayed at Fulham to begin with!",
                    "can_remove": False,
                    "created_time": "2013-12-20T16:25:26+0000",
                    "like_count": 0,
                    "user_likes": False
                },
            ]},
            {"data": [
                {
                    "id": "100002382106641",
                    "name": "Joseph Orozco"
                },
            ]},
        ]
        user_feed = json.loads(
            open(os.path.join(DATA_PATH, 'user_feed.json')).read()
        )
        self.assertEqual(len(user_feed['data'][0]['comments']['data']), 1)
        self.assertEqual(len(user_feed['data'][0]['likes']['data']), 3)
        s3_key_mock = Mock()
        tasks.crawl_comments_and_likes(user_feed, s3_key_mock)
        extended_feed = json.loads(
            s3_key_mock.set_contents_from_string.call_args[0][0]
        )
        self.assertEqual(len(extended_feed['data'][0]['comments']['data']), 2)
        self.assertEqual(len(extended_feed['data'][0]['likes']['data']), 4)
