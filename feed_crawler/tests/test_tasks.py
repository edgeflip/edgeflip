import os
import json
import urllib2
from datetime import timedelta

from mock import Mock, patch

from django.utils import timezone
from faraday.utils import epoch

from targetshare import models
from targetshare.tests import EdgeFlipTestCase, crawl_mock

from feed_crawler import tasks, s3_feed

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def mock_feed(url):
    if '/feed' in url:
        return {'data': [{'ooga': 'booga'}]}


class TestFeedCrawlerTasks(EdgeFlipTestCase):

    def setUp(self):
        super(TestFeedCrawlerTasks, self).setUp()

        self.fbid = 1111111
        expires = timezone.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.token = models.dynamo.Token.items.create(
            fbid=self.fbid, appid=1, token='1', expires=expires)

        self.facebook_patch = patch(
            'targetshare.integration.facebook.client.urllib2.urlopen',
            crawl_mock(1, 250, mock_feed)
        )
        self.token_patch = patch(
            'targetshare.integration.facebook.client.debug_token',
            return_value={
                'data': {
                    'is_valid': True,
                    'expires_at': expires,
                }
            }
        )
        self.facebook_patch.start()
        self.token_patch.start()

    def tearDown(self):
        self.token_patch.stop()
        self.facebook_patch.stop()
        super(TestFeedCrawlerTasks, self).tearDown()

    @patch('feed_crawler.tasks.initial_crawl')
    @patch('feed_crawler.tasks.incremental_crawl')
    def test_crawl_user(self, incremental_mock, initial_mock):
        models.FBSyncMap.items.create(
            fbid_primary=self.fbid, fbid_secondary=self.fbid, token=self.token.token,
            back_filled=False, back_fill_epoch=0, incremental_epoch=0,
            status=models.FBSyncMap.COMPLETE, bucket='test_bucket_0'
        )
        models.FBSyncMap.items.create(
            fbid_primary=self.fbid, fbid_secondary=self.fbid + 1, token=self.token.token,
            back_filled=False, back_fill_epoch=0, incremental_epoch=0,
            status=models.FBSyncMap.QUEUED, bucket='test_bucket_0'
        )
        tasks.crawl_user(self.token.fbid, self.token.appid)
        self.assertTrue(initial_mock.apply_async.called)
        self.assertGreater(initial_mock.apply_async.call_count, 1)
        self.assertEqual(incremental_mock.apply_async.call_count, 1)
        self.assertGreater(models.FBSyncMap.items.count(), 1)

    def test_bg_px4_crawl(self):
        self.assertFalse(models.dynamo.IncomingEdge.items.count())
        self.assertFalse(models.dynamo.PostInteractions.items.count())
        self.assertFalse(models.dynamo.PostInteractionsSet.items.count())

        ranked_edges = tasks._bg_px4_crawl(self.token)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)
        assert all(x.incoming.post_likes is not None for x in ranked_edges)

        self.assertTrue(models.dynamo.IncomingEdge.items.count())
        self.assertTrue(models.dynamo.PostInteractions.items.count())
        self.assertTrue(models.dynamo.PostInteractionsSet.items.count())
        # We know we have a call to get the user and the friend count at the
        # very least. However, hitting FB should spawn many more hits to FB
        self.assertGreater(urllib2.urlopen.call_count, 2)

    def test_get_sync_maps(self):
        self.assertFalse(models.FBSyncMap.items.count())
        edges = tasks._bg_px4_crawl(self.token)
        tasks._get_sync_maps(edges, self.token)
        models.FBSyncMap.items.get_item(fbid_primary=self.fbid,
                                        fbid_secondary=self.fbid)
        self.assertGreater(models.FBSyncMap.items.count(), 1)

    @patch('feed_crawler.tasks.back_fill_crawl')
    @patch('feed_crawler.s3_feed.S3Manager.get_bucket')
    @patch('feed_crawler.s3_feed.BucketManager.get_key')
    @patch('feed_crawler.s3_feed.BucketManager.new_key')
    def test_initial_crawl(self, new_bucket_mock, bucket_mock, conn_mock, crawl_mock):
        fbm = models.FBSyncMap.items.create(
            fbid_primary=self.fbid, fbid_secondary=self.fbid, token=self.token.token,
            back_filled=False, back_fill_epoch=0, incremental_epoch=0,
            status=models.FBSyncMap.WAITING, bucket='test_bucket_0'
        )
        new_key = Mock()
        new_key.data = {'data': []}
        new_bucket_mock.return_value = new_key
        bucket_mock.return_value = None
        conn_mock.return_value = s3_feed.BucketManager()
        tasks.initial_crawl(fbm.fbid_primary, fbm.fbid_secondary)
        fbm = models.FBSyncMap.items.get_item(
            fbid_primary=self.fbid, fbid_secondary=self.fbid)
        self.assertEqual(fbm.status, fbm.BACK_FILL)
        assert fbm.back_fill_epoch
        assert fbm.incremental_epoch
        self.assertTrue(new_key.save_to_s3.called)

    @patch('feed_crawler.tasks.crawl_comments_and_likes')
    @patch('feed_crawler.s3_feed.S3Manager.get_bucket')
    @patch('feed_crawler.s3_feed.BucketManager.get_key')
    def test_back_fill_crawl(self, bucket_mock, conn_mock, crawl_mock):
        the_past = epoch.from_date(timezone.now() - timedelta(days=365))
        fbm = models.FBSyncMap.items.create(
            fbid_primary=self.fbid, fbid_secondary=self.fbid, token=self.token.token,
            back_filled=False, back_fill_epoch=the_past,
            incremental_epoch=epoch.from_date(timezone.now()),
            status=models.FBSyncMap.BACK_FILL, bucket='test_bucket_0'
        )
        existing_key = Mock()
        existing_key.data = {"updated": 1, "data": [{"test": "testing"}]}
        bucket_mock.return_value = existing_key
        conn_mock.return_value = s3_feed.BucketManager()
        tasks.back_fill_crawl(fbm.fbid_primary, fbm.fbid_secondary)
        fbm = models.FBSyncMap.items.get_item(
            fbid_primary=self.fbid, fbid_secondary=self.fbid)
        self.assertEqual(fbm.status, fbm.COMMENT_CRAWL)
        assert fbm.back_fill_epoch
        assert fbm.back_filled
        assert fbm.incremental_epoch
        assert crawl_mock.apply_async.called
        self.assertTrue(existing_key.extend_s3_data.called)

    @patch('feed_crawler.s3_feed.S3Manager.get_bucket')
    @patch('feed_crawler.s3_feed.BucketManager.get_key')
    def test_incremental_crawl(self, bucket_mock, conn_mock):
        the_past = epoch.from_date(timezone.now() - timedelta(days=365))
        # Test runs in under a second typically, so we need to be slightly
        # behind present time, so that we can see fbm.incremental_epoch
        # get updated
        present = epoch.from_date(timezone.now() - timedelta(seconds=30))
        fbm = models.FBSyncMap.items.create(
            fbid_primary=self.fbid, fbid_secondary=self.fbid, token=self.token.token,
            back_filled=False, back_fill_epoch=the_past,
            incremental_epoch=present,
            status=models.FBSyncMap.COMPLETE, bucket='test_bucket_0'
        )
        existing_key = Mock()
        existing_key.data = {"updated": 1, "data": [{"test": "testing"}]}
        bucket_mock.return_value = existing_key
        conn_mock.return_value = s3_feed.BucketManager()
        tasks.incremental_crawl(fbm.fbid_primary, fbm.fbid_secondary)
        new_fbm = models.FBSyncMap.items.get_item(
            fbid_primary=self.fbid, fbid_secondary=self.fbid)
        self.assertEqual(fbm.status, fbm.COMPLETE)
        self.assertGreater(int(new_fbm.incremental_epoch), present)
        self.assertTrue(existing_key.extend_s3_data.called)
        self.assertSequenceEqual(
            existing_key.extend_s3_data.call_args_list[0][0],
            (False,)
        )

    @patch('feed_crawler.tasks.incremental_crawl')
    @patch('feed_crawler.s3_feed.S3Manager.get_bucket')
    @patch('feed_crawler.s3_feed.BucketManager.get_key')
    def test_incremental_crawl_failure(self, bucket_mock, conn_mock, crawl_mock):
        def failure_feed(url):
            if '/feed' in url:
                return {'notdata': [{'ooga': 'booga'}]}
        self.facebook_patch = patch(
            'targetshare.integration.facebook.client.urllib2.urlopen',
            crawl_mock(1, 250, failure_feed)
        )
        self.facebook_patch.start()
        the_past = epoch.from_date(timezone.now() - timedelta(days=365))
        # Test runs in under a second typically, so we need to be slightly
        # behind present time, so that we can see fbm.incremental_epoch
        # get updated
        present = epoch.from_date(timezone.now() - timedelta(seconds=30))
        fbm = models.FBSyncMap.items.create(
            fbid_primary=self.fbid, fbid_secondary=self.fbid, token=self.token.token,
            back_filled=False, back_fill_epoch=the_past,
            incremental_epoch=present,
            status=models.FBSyncMap.COMPLETE, bucket='test_bucket_0'
        )
        existing_key = Mock()
        existing_key.get_contents_as_string.return_value = '{"updated": 1, "data": [{"test": "testing"}]}'
        bucket_mock.return_value = existing_key
        conn_mock.return_value = s3_feed.BucketManager()
        tasks.incremental_crawl(fbm.fbid_primary, fbm.fbid_secondary)
        new_fbm = models.FBSyncMap.items.get_item(
            fbid_primary=self.fbid, fbid_secondary=self.fbid)
        self.assertEqual(fbm.status, fbm.COMPLETE)
        self.assertEqual(int(new_fbm.incremental_epoch), present)
        self.assertFalse(existing_key.set_contents_from_string.called)

    @patch('targetshare.integration.facebook.client.urlload')
    @patch('feed_crawler.s3_feed.S3Manager.get_bucket')
    @patch('feed_crawler.s3_feed.BucketManager.get_key')
    def test_crawl_comments_and_likes(self, bucket_mock, conn_mock, fb_mock):
        the_past = epoch.from_date(timezone.now() - timedelta(days=365))
        fbm = models.FBSyncMap.items.create(
            fbid_primary=self.fbid, fbid_secondary=self.fbid, token=self.token.token,
            back_filled=False, back_fill_epoch=the_past,
            incremental_epoch=epoch.from_date(timezone.now()),
            status=models.FBSyncMap.COMMENT_CRAWL, bucket='test_bucket_0'
        )
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
        existing_key.data = json.load(
            open(os.path.join(DATA_PATH, 'user_feed.json'))
        )
        bucket_mock.return_value = existing_key
        conn_mock.return_value = s3_feed.BucketManager()
        self.assertEqual(len(user_feed['data'][0]['comments']['data']), 1)
        self.assertEqual(len(user_feed['data'][0]['likes']['data']), 3)
        tasks.crawl_comments_and_likes(fbm.fbid_primary, fbm.fbid_secondary)
        self.assertEqual(len(existing_key.data['data'][0]['comments']['data']), 2)
        self.assertEqual(len(existing_key.data['data'][0]['likes']['data']), 4)
        fbm = models.FBSyncMap.items.get_item(fbid_primary=self.fbid,
                                              fbid_secondary=self.fbid)
        self.assertEqual(fbm.status, fbm.COMPLETE)
