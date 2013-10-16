import datetime
import os.path

from django.core.cache import cache
from django.utils import timezone, unittest
from django.test import TestCase
from mock import Mock, patch

from targetshare.management.commands import seedfbobject
from targetshare.models import relational
from targetshare.tests import DATA_PATH


GG_FIXTURE = open(os.path.join(DATA_PATH, 'gg.html')).read()


class SeedingTestMixIn(object):

    requests_patch = None

    @classmethod
    def setUpClass(cls):
        cls.requests_patch = patch(
            'targetshare.integration.facebook.third_party.requests.get',
            side_effect=(Mock(text=GG_FIXTURE),) * 2
        )

    def setUp(self):
        super(SeedingTestMixIn, self).setUp()
        self.command = seedfbobject.Command()

        self.urls = ('http://foo.com/1/', 'http://foo.com/2/')
        for url in self.urls:
            cache.delete('fbobject|{}'.format(url))

        self.requests_patch.start()

    def tearDown(self):
        self.requests_patch.stop()
        super(SeedingTestMixIn, self).tearDown()


class TestSeedCache(SeedingTestMixIn, unittest.TestCase):

    def test_seed_arguments(self):
        self.command.handle(urls=self.urls)

        for url in self.urls:
            meta = cache.get('fbobject|{}'.format(url))
            self.assertEqual(meta['og:title'], "Scholarship for Filipino Midwife Student")
            self.assertEqual(meta['og:description'][:22], "The Philippines, like ")
            self.assertEqual(meta['og:image'],
                "https://dpqe0zkrjo0ak.cloudfront.net/pfil/14426/pict_grid7.jpg")
            self.assertEqual(meta['og:site_name'], "GlobalGiving.org")

    def test_seed_stdin(self):
        stdin = (url + '\n' for url in self.urls)
        with patch.object(seedfbobject.sys, 'stdin', **{'xreadlines.return_value': stdin}):
            self.command.handle()

        for url in self.urls:
            meta = cache.get('fbobject|{}'.format(url))
            self.assertEqual(meta['og:title'], "Scholarship for Filipino Midwife Student")
            self.assertEqual(meta['og:description'][:22], "The Philippines, like ")
            self.assertEqual(meta['og:image'],
                "https://dpqe0zkrjo0ak.cloudfront.net/pfil/14426/pict_grid7.jpg")
            self.assertEqual(meta['og:site_name'], "GlobalGiving.org")


class TestSeedDb(SeedingTestMixIn, TestCase):

    fixtures = ('test_data',)

    def test_seed_arguments(self):
        self.command.handle(campaign_id=1, urls=self.urls)

        for url in self.urls:
            self.assertTrue(cache.get('fbobject|{}'.format(url)))
            campaign_fbobject = relational.CampaignFBObject.objects.get(campaign_id=1,
                                                                        source_url=url)
            fb_object = campaign_fbobject.fb_object
            self.assertTrue(fb_object.fbobjectattribute_set.for_datetime().exists())
            one_minute_ago = timezone.now() - datetime.timedelta(minutes=1)
            self.assertGreater(campaign_fbobject.sourced, one_minute_ago)

    def test_seed_stdin(self):
        stdin = ("{} 1\n".format(url) for url in self.urls)
        with patch.object(seedfbobject.sys, 'stdin', **{'xreadlines.return_value': stdin}):
            self.command.handle()

        for url in self.urls:
            self.assertTrue(cache.get('fbobject|{}'.format(url)))
            campaign_fbobject = relational.CampaignFBObject.objects.get(campaign_id=1,
                                                                        source_url=url)
            fb_object = campaign_fbobject.fb_object
            self.assertTrue(fb_object.fbobjectattribute_set.for_datetime().exists())
            one_minute_ago = timezone.now() - datetime.timedelta(minutes=1)
            self.assertGreater(campaign_fbobject.sourced, one_minute_ago)
