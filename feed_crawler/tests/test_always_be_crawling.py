from mock import patch
from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone

from targetshare.models import dynamo
from targetshare.tests import EdgeFlipTestCase


class TestAlwaysBeCrawling(EdgeFlipTestCase):

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
        call_command('always_be_crawling')
        self.assertEqual(crawl_mock.delay.call_count, 2)

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
        call_command('always_be_crawling')
        self.assertEqual(crawl_mock.call_count, 0)
