import os
import json
import urllib2
from datetime import timedelta

from mock import Mock, patch

from django.utils import timezone

from targetshare import models
from targetshare.models.dynamo.utils import to_epoch
from targetshare.tests import EdgeFlipTestCase, patch_facebook

from feed_crawler import tasks, utils

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


class TestFeedCrawlerTasks(EdgeFlipTestCase):

    def setUp(self):
        super(TestFeedCrawlerTasks, self).setUp()
        expires = timezone.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.fbid = 1111111
        self.token = models.dynamo.Token(fbid=self.fbid, appid=1,
                                         token='1', expires=expires)

    @patch_facebook(min_friends=1, max_friends=20)
    @patch('feed_crawler.tasks.initial_crawl')
    @patch('feed_crawler.tasks.incremental_crawl')
    def test_crawl_user(self, incremental_mock, initial_mock):
        prim_fbm = models.FBSyncMap(
            fbid_primary=self.fbid, fbid_secondary=self.fbid, token=self.token.token,
            back_filled=0, back_fill_epoch=0, incremental_epoch=0,
            status=models.FBSyncMap.COMPLETE, bucket='test_bucket_0'
        )
        prim_fbm.save()
        tasks.crawl_user(self.token)
        self.assertTrue(initial_mock.apply_async.called)
        self.assertGreater(initial_mock.apply_async.call_count, 1)
        self.assertEqual(incremental_mock.apply_async.call_count, 1)
        self.assertGreater(len(models.FBSyncMap.items.scan()), 1)

    @patch_facebook(min_friends=1, max_friends=20)
    def test_bg_px4_crawl(self):
        self.assertFalse(models.dynamo.IncomingEdge.items.scan(limit=1))

        ranked_edges = tasks._bg_px4_crawl(self.token)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)
        assert all(x.incoming.post_likes is not None for x in ranked_edges)

        self.assertTrue(models.dynamo.IncomingEdge.items.scan(limit=1))
        # We know we have a call to get the user and the friend count at the
        # very least. However, hitting FB should spawn many more hits to FB
        self.assertGreater(urllib2.urlopen.call_count, 2)

    @patch_facebook(min_friends=1, max_friends=20)
    def test_get_sync_maps(self):
        self.assertFalse(models.FBSyncMap.items.scan())
        edges = tasks._bg_px4_crawl(self.token)
        tasks._get_sync_maps(edges, self.token)
        assert models.FBSyncMap.items.get_item(
            fbid_primary=self.fbid, fbid_secondary=self.fbid)
        self.assertGreater(len(models.FBSyncMap.items.scan()), 1)

    @patch_facebook
    @patch('feed_crawler.utils.S3Manager.get_bucket')
    @patch('feed_crawler.utils.BucketManager.get_key')
    @patch('feed_crawler.utils.BucketManager.new_key')
    def test_initial_crawl(self, new_bucket_mock, bucket_mock, conn_mock):
        fbm = models.FBSyncMap(
            fbid_primary=self.fbid, fbid_secondary=self.fbid, token=self.token.token,
            back_filled=0, back_fill_epoch=0, incremental_epoch=0,
            status=models.FBSyncMap.WAITING, bucket='test_bucket_0'
        )
        fbm.save()
        new_key = Mock()
        new_bucket_mock.return_value = new_key
        bucket_mock.return_value = None
        conn_mock.return_value = utils.BucketManager()
        tasks.initial_crawl(fbm)
        fbm = models.FBSyncMap.items.get_item(
            fbid_primary=self.fbid, fbid_secondary=self.fbid)
        self.assertEqual(fbm.status, fbm.BACK_FILL)
        assert fbm.back_fill_epoch
        assert fbm.incremental_epoch
        self.assertTrue(new_key.set_contents_from_string.called)

    @patch_facebook
    @patch('feed_crawler.utils.S3Manager.get_bucket')
    @patch('feed_crawler.utils.BucketManager.get_key')
    def test_back_fill_crawl(self, bucket_mock, conn_mock):
        the_past = to_epoch(timezone.now() - timedelta(days=365))
        fbm = models.FBSyncMap(
            fbid_primary=self.fbid, fbid_secondary=self.fbid, token=self.token.token,
            back_filled=0, back_fill_epoch=the_past,
            incremental_epoch=to_epoch(timezone.now()),
            status=models.FBSyncMap.BACK_FILL, bucket='test_bucket_0'
        )
        fbm.save()
        existing_key = Mock()
        existing_key.get_contents_as_string.return_value = '{"updated": 1, "data": [{"test": "testing"}]}'
        bucket_mock.return_value = existing_key
        conn_mock.return_value = utils.BucketManager()
        tasks.back_fill_crawl(fbm)
        fbm = models.FBSyncMap.items.get_item(
            fbid_primary=self.fbid, fbid_secondary=self.fbid)
        self.assertEqual(fbm.status, fbm.COMPLETE)
        assert fbm.back_fill_epoch
        assert fbm.incremental_epoch
        self.assertTrue(existing_key.set_contents_from_string.called)

    @patch_facebook
    @patch('feed_crawler.utils.S3Manager.get_bucket')
    @patch('feed_crawler.utils.BucketManager.get_key')
    def test_incremental_crawl(self, bucket_mock, conn_mock):
        the_past = to_epoch(timezone.now() - timedelta(days=365))
        # Test runs in under a second typically, so we need to be slightly
        # behind present time, so that we can see fbm.incremental_epoch
        # get updated
        present = to_epoch(timezone.now() - timedelta(seconds=30))
        fbm = models.FBSyncMap(
            fbid_primary=self.fbid, fbid_secondary=self.fbid, token=self.token.token,
            back_filled=0, back_fill_epoch=the_past,
            incremental_epoch=present,
            status=models.FBSyncMap.COMPLETE, bucket='test_bucket_0'
        )
        fbm.save()
        existing_key = Mock()
        existing_key.get_contents_as_string.return_value = '{"updated": 1, "data": [{"test": "testing"}]}'
        bucket_mock.return_value = existing_key
        conn_mock.return_value = utils.BucketManager()
        tasks.incremental_crawl(fbm)
        new_fbm = models.FBSyncMap.items.get_item(
            fbid_primary=self.fbid, fbid_secondary=self.fbid)
        self.assertEqual(fbm.status, fbm.COMPLETE)
        self.assertGreater(int(new_fbm.incremental_epoch), present)
        self.assertTrue(existing_key.set_contents_from_string.called)

    @patch('targetshare.integration.facebook.client.urlload')
    @patch('feed_crawler.utils.S3Manager.get_bucket')
    @patch('feed_crawler.utils.BucketManager.get_key')
    def test_crawl_comments_and_likes(self, bucket_mock, conn_mock, fb_mock):
        the_past = to_epoch(timezone.now() - timedelta(days=365))
        fbm = models.FBSyncMap(
            fbid_primary=self.fbid, fbid_secondary=self.fbid, token=self.token.token,
            back_filled=0, back_fill_epoch=the_past,
            incremental_epoch=to_epoch(timezone.now()),
            status=models.FBSyncMap.COMMENT_CRAWL, bucket='test_bucket_0'
        )
        fbm.save()
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
        existing_key = Mock()
        existing_key.get_contents_as_string.return_value = open(
            os.path.join(DATA_PATH, 'user_feed.json')).read()
        bucket_mock.return_value = existing_key
        conn_mock.return_value = utils.BucketManager()
        self.assertEqual(len(user_feed['data'][0]['comments']['data']), 1)
        self.assertEqual(len(user_feed['data'][0]['likes']['data']), 3)
        tasks.crawl_comments_and_likes(fbm)
        extended_feed = json.loads(
            existing_key.set_contents_from_string.call_args[0][0]
        )
        self.assertEqual(len(extended_feed['data'][0]['comments']['data']), 2)
        self.assertEqual(len(extended_feed['data'][0]['likes']['data']), 4)
        fbm = models.FBSyncMap.items.get_item(
            fbid_primary=self.fbid, fbid_secondary=self.fbid)
        self.assertEqual(fbm.status, fbm.COMPLETE)
