from mock import Mock, patch

from django.utils import timezone

from targetshare.tests import EdgeFlipTestCase, patch_facebook
from targetshare.tasks.ranking import px3_crawl
from targetshare import models

from feed_crawler import tasks, utils


class TestFeedCrawlerTasks(EdgeFlipTestCase):

    def setUp(self):
        super(TestFeedCrawlerTasks, self).setUp()
        expires = timezone.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.token = models.dynamo.Token(fbid=1, appid=1, token='1', expires=expires)

    @patch_facebook
    @patch('feed_crawler.tasks.process_sync_task')
    def test_create_sync_task(self, sync_mock):
        ''' Should create a FBTaskSync object and place a process_sync_task
        job on the queue
        '''
        edges = px3_crawl(False, 1, self.token)
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
        edges = px3_crawl(False, 1, self.token)
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
        tasks.process_sync_task(1)
        self.assertTrue(new_key.set_contents_from_string.called)
        fbt = models.FBSyncTask.items.get_item(fbid=1)
        self.assertEqual(fbt.status, models.FBSyncTask.COMPLETED)
        self.assertEqual(fbt.fbids_to_crawl, None)

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
        tasks.process_sync_task(1)
        self.assertTrue(existing_key.get_contents_as_string.called)
        self.assertTrue(existing_key.set_contents_from_string.called)
        fbt = models.FBSyncTask.items.get_item(fbid=1)
        self.assertEqual(fbt.status, models.FBSyncTask.COMPLETED)
        self.assertEqual(fbt.fbids_to_crawl, None)
