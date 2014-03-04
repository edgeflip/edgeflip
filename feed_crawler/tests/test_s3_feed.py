import os
import shutil
import unittest

from mock import patch

from feed_crawler import s3_feed

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def get_contents_to_filename(cls, filename):
    shutil.copyfile(os.path.join(DATA_PATH, 'user_feed.json'), filename)


class TestFeedKey(unittest.TestCase):

    def setUp(self):
        self.key = s3_feed.FeedKey()
        super(TestFeedKey, self).setUp()

    @patch('feed_crawler.s3_feed.facebook.client.urlload')
    def test_retrieve_fb_feed(self, fb_mock):
        fb_data = {'data': [{1: 'some_data'}]}
        fb_mock.return_value = fb_data
        self.key.retrieve_fb_feed(1, '1', 1, 1)
        self.assertEqual(self.key.data, fb_data)

    @patch('feed_crawler.s3_feed.facebook.client.exhaust_pagination')
    def test_crawl_pagination(self, fb_mock):
        self.key.data = {
            'data': [{1: 'some_data'}],
            'paging': {'next': 'some_url'},
        }
        fb_mock.return_value = {'data': [{2: 'more_data'}]}
        self.key.crawl_pagination()
        self.assertEqual(len(self.key.data), 2)

    @patch('feed_crawler.s3_feed.FeedKey.set_contents_from_filename')
    def test_save_to_s3(self, upload_mock):
        self.key.data = {
            'data': [{1: 'some_data'}],
            'paging': {'next': 'some_url'},
        }
        self.key.save_to_s3()
        self.assertTrue(self.key.set_contents_from_filename.called)
        self.assertIn(
            'tmp', self.key.set_contents_from_filename.call_args[0][0]
        )

    @patch('feed_crawler.s3_feed.FeedKey.get_contents_to_filename', get_contents_to_filename)
    @patch('feed_crawler.s3_feed.FeedKey.set_contents_from_filename')
    def test_append_data_to_s3(self, upload_mock):
        self.key.data = {
            'data': [{1: 'some_data'}],
            'paging': {'next': 'some_url'},
        }
        self.key.extend_s3_data()
        self.assertTrue(upload_mock.called)
        self.assertGreater(len(self.key.data['data']), 1)
        self.assertEqual(self.key.data['data'][0]['id'], '1357997116_10202851367949409')
        self.assertEqual(self.key.data['data'][1][1], 'some_data')

    @patch('feed_crawler.s3_feed.FeedKey.get_contents_to_filename', get_contents_to_filename)
    @patch('feed_crawler.s3_feed.FeedKey.set_contents_from_filename')
    def test_prepend_data_to_s3(self, upload_mock):
        self.key.data = {
            'data': [{1: 'some_data'}],
            'paging': {'next': 'some_url'},
        }
        self.key.extend_s3_data(False)
        self.assertTrue(upload_mock.called)
        self.assertGreater(len(self.key.data['data']), 1)
        self.assertEqual(self.key.data['data'][0][1], 'some_data')
        self.assertEqual(self.key.data['data'][1]['id'], '1357997116_10202851367949409')

    @patch('feed_crawler.s3_feed.FeedKey.get_contents_to_filename', get_contents_to_filename)
    def test_populate_from_s3(self):
        self.key.data = {}
        self.key.populate_from_s3()
        self.assertEqual(len(self.key.data['data']), 1)
