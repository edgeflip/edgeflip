from mock import Mock

from feed_crawler.management.commands import always_be_crawling
from targetshare.tests import EdgeFlipTestCase


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
