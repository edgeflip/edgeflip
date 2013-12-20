from mock import Mock, patch
from datetime import timedelta

from django.utils import timezone

from feed_crawler.management.commands import always_be_crawling
from targetshare.tests import EdgeFlipTestCase
from targetshare.models import dynamo


class TestAlwaysBeCrawling(EdgeFlipTestCase):

    def setUp(self):
        super(TestAlwaysBeCrawling, self).setUp()
        self.command = always_be_crawling.Command()

    def test_handle(self):
        orig_crawl = self.command.crawl
        crawl_mock = Mock()
        self.command.crawl = crawl_mock
        self.command.handle()
        self.assertTrue(crawl_mock.called)
        self.command.crawl = orig_crawl

    @patch('feed_crawler.tasks.crawl_user')
    def test_crawl(self, crawl_mock):
        the_future = timezone.now() + timedelta(days=5)
        dynamo.Token(
            fbid=12345, appid=1,
            expires=the_future, token='test'
        ).save()
        dynamo.Token(
            fbid=67890, appid=1,
            expires=the_future, token='test'
        ).save()
        self.command.crawl()
        self.assertEqual(crawl_mock.call_count, 2)

    @patch('feed_crawler.tasks.crawl_user')
    def test_crawl_expired_tokens(self, crawl_mock):
        dynamo.Token(
            fbid=12345, appid=1,
            expires=1, token='test'
        ).save()
        dynamo.Token(
            fbid=67890, appid=1,
            expires=1, token='test'
        ).save()
        self.command.crawl()
        self.assertEqual(crawl_mock.call_count, 0)
