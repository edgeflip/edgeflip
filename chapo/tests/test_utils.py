from datetime import datetime, timedelta

from django.test import TestCase
from mock import patch

from targetshare.models.relational import Client

from chapo import models, utils
from chapo.tests import urandom_patch, BYTES, BYTES2


URL = "http://www.reddit.com/r/food/"

chapo_settings = patch('django.conf.settings.CHAPO_SERVER', 'http://edgefl.ip', create=True)


class DictCache(dict):

    __slots__ = ()

    def set(self, key, value, timeout=None):
        self[key] = value


class TestShortUrl(TestCase):

    def test_short_url(self):
        """short_url returns the shortened URL of a ShortenedUrl object"""
        short = models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL)
        out = utils.short_url(short)
        self.assertEqual(out, "/r/ooga-booga/")

    @chapo_settings
    def test_server_setting(self):
        """short_url constructs absolute URLs from the CHAPO_SERVER setting"""
        short = models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL)
        out = utils.short_url(short)
        self.assertEqual(out, "http://edgefl.ip/r/ooga-booga/")

    @chapo_settings
    def test_server(self):
        """short_url constructs absolute URLs from the server argument"""
        short = models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL)
        out = utils.short_url(short, server='//app.edgeflip.com')
        self.assertEqual(out, "//app.edgeflip.com/r/ooga-booga/")

    def test_slug(self):
        """short_url returns the shortened URL for a ShortenedUrl slug"""
        out = utils.short_url('ooga-booga')
        self.assertEqual(out, "/r/ooga-booga/")


class TestShorten(TestCase):

    @urandom_patch
    def test_shorten(self, _mock):
        shorts = models.ShortenedUrl.objects.values('campaign_id', 'event_type', 'slug', 'url')
        self.assertEqual(shorts.count(), 0)
        out = utils.shorten('http://www.english.com/alphabet/a/b/c/d/efgh/')
        self.assertEqual(out, "/r/jSgnUTqptPrV/")
        self.assertEqual(shorts.get(), {
            'campaign_id': None,
            'event_type': 'initial_redirect',
            'slug': 'jSgnUTqptPrV',
            'url': 'http://www.english.com/alphabet/a/b/c/d/efgh/',
        })

    @urandom_patch
    def test_prefix(self, _mock):
        shorts = models.ShortenedUrl.objects.values('campaign_id', 'event_type', 'slug', 'url')
        self.assertEqual(shorts.count(), 0)
        out = utils.shorten('http://www.english.com/alphabet/a/b/c/d/efgh/', prefix='en')
        self.assertEqual(out, "/r/en-jSgnUTqpt/")
        self.assertEqual(shorts.get(), {
            'campaign_id': None,
            'event_type': 'initial_redirect',
            'slug': 'en-jSgnUTqpt',
            'url': 'http://www.english.com/alphabet/a/b/c/d/efgh/',
        })

    @patch('os.urandom', side_effect=(BYTES, BYTES, BYTES2))
    @patch('chapo.utils.LOG')
    def test_retry(self, log_mock, _urandom_mock):
        models.ShortenedUrl.objects.create(url=URL) # pre-existing
        shorts = models.ShortenedUrl.objects.values('campaign_id', 'event_type', 'slug', 'url')
        self.assertEqual(shorts.count(), 1)

        out = utils.shorten('http://www.english.com/alphabet/a/b/c/d/efgh/')
        self.assertEqual(out, "/r/WSTUhHUshgrt/")

        self.assertEqual(shorts.count(), 2)
        self.assertEqual(shorts.exclude(slug='jSgnUTqptPrV').get(), {
            'campaign_id': None,
            'event_type': 'initial_redirect',
            'slug': 'WSTUhHUshgrt',
            'url': 'http://www.english.com/alphabet/a/b/c/d/efgh/',
        })
        log_mock.warning.assert_called_once_with("shorten required %s attempts", 2)

    @urandom_patch
    @patch('django.core.cache.cache',
           {'shorturl|initial_redirect|||cc06be0890c05085b3fbeec2bea1ad9d': 'jSgnUTqptPrV'})
    def test_cache(self, _urandom_mock):
        """shorten checks cache for existing ShortenedUrl slug"""
        shorts = models.ShortenedUrl.objects.all()
        self.assertEqual(shorts.count(), 0)
        out = utils.shorten('http://www.reddit.com/r/food/')
        self.assertEqual(out, "/r/jSgnUTqptPrV/")
        self.assertEqual(shorts.count(), 0)

    @urandom_patch
    @patch('django.core.cache.cache',
           {'shorturl|initial_redirect|food||cc06be0890c05085b3fbeec2bea1ad9d': 'food-jSgnUTqp'})
    def test_cache_prefix(self, _urandom_mock):
        """shorten checks cache for existing ShortenedUrl slug and respects prefix"""
        shorts = models.ShortenedUrl.objects.all()
        self.assertEqual(shorts.count(), 0)
        out = utils.shorten('http://www.reddit.com/r/food/', prefix='food')
        self.assertEqual(out, "/r/food-jSgnUTqp/")
        self.assertEqual(shorts.count(), 0)

    @urandom_patch
    @patch('django.core.cache.cache',
           {'shorturl|initial_redirect||1|cc06be0890c05085b3fbeec2bea1ad9d': 'jSgnUTqptPrV'})
    def test_cache_campaign_id(self, _urandom_mock):
        """shorten checks cache for existing ShortenedUrl slug and respects campaign ID"""
        shorts = models.ShortenedUrl.objects.all()
        self.assertEqual(shorts.count(), 0)
        out = utils.shorten('http://www.reddit.com/r/food/', campaign=1)
        self.assertEqual(out, "/r/jSgnUTqptPrV/")
        self.assertEqual(shorts.count(), 0)

    @urandom_patch
    @patch('django.core.cache.cache',
           {'shorturl|initial_redirect||1|cc06be0890c05085b3fbeec2bea1ad9d': 'jSgnUTqptPrV'})
    def test_cache_campaign(self, _urandom_mock):
        """shorten checks cache for existing ShortenedUrl slug and respects Campaign"""
        client = Client.objects.create(codename='testerson')
        campaign = client.campaigns.create(campaign_id=1)

        shorts = models.ShortenedUrl.objects.all()
        self.assertEqual(shorts.count(), 0)
        out = utils.shorten('http://www.reddit.com/r/food/', campaign=campaign)
        self.assertEqual(out, "/r/jSgnUTqptPrV/")
        self.assertEqual(shorts.count(), 0)

    @urandom_patch
    def test_cache_set(self, _urandom_mock):
        """shorten populates cache with ShortenedUrl slug"""
        client = Client.objects.create(codename='testerson')
        campaign = client.campaigns.create(campaign_id=1)

        shorts = models.ShortenedUrl.objects.values('campaign_id', 'event_type', 'slug', 'url')
        self.assertEqual(shorts.count(), 0)

        cache = DictCache()
        self.assertEqual(len(cache), 0)

        with patch('django.core.cache.cache', cache):
            out = utils.shorten('http://www.reddit.com/r/food/', 'food', campaign)

        self.assertEqual(out, "/r/food-jSgnUTqp/")
        self.assertEqual(shorts.count(), 1)
        self.assertEqual(shorts.get(), {
            'slug': 'food-jSgnUTqp',
            'campaign_id': 1,
            'event_type': 'initial_redirect',
            'url': 'http://www.reddit.com/r/food/',
        })

        self.assertEqual(len(cache), 1)

        slug = cache['shorturl|initial_redirect|food|1|cc06be0890c05085b3fbeec2bea1ad9d']
        self.assertEqual(slug, 'food-jSgnUTqp')

    @urandom_patch
    def test_read_db(self, _mock):
        models.ShortenedUrl.objects.create(slug='testIslug', url=URL)
        shorts = models.ShortenedUrl.objects.all()
        self.assertEqual(shorts.count(), 1)

        cache = DictCache()
        self.assertEqual(len(cache), 0)

        with patch('django.core.cache.cache', cache):
            out = utils.shorten(URL, event_type='generic_redirect')

        self.assertEqual(out, "/r/testIslug/")
        self.assertEqual(shorts.count(), 1)

        self.assertEqual(len(cache), 1)

        slug = cache['shorturl|generic_redirect|||cc06be0890c05085b3fbeec2bea1ad9d']
        self.assertEqual(slug, 'testIslug')

    @urandom_patch
    def test_read_db_event_type(self, _mock):
        models.ShortenedUrl.objects.create(event_type='initial_redirect', slug='testIslug', url=URL)
        shorts = models.ShortenedUrl.objects.all()
        self.assertEqual(shorts.count(), 1)

        cache = DictCache()
        self.assertEqual(len(cache), 0)

        with patch('django.core.cache.cache', cache):
            out = utils.shorten(URL)

        self.assertEqual(out, "/r/testIslug/")
        self.assertEqual(shorts.count(), 1)

        self.assertEqual(len(cache), 1)

        slug = cache['shorturl|initial_redirect|||cc06be0890c05085b3fbeec2bea1ad9d']
        self.assertEqual(slug, 'testIslug')

    @urandom_patch
    def test_read_db_campaign(self, _mock):
        client = Client.objects.create(codename='testerson')
        campaign = client.campaigns.create(campaign_id=1)

        campaign.shortenedurls.create(
            event_type='initial_redirect',
            slug='testIslug',
            url=URL,
        )
        shorts = models.ShortenedUrl.objects.all()
        self.assertEqual(shorts.count(), 1)

        cache = DictCache()
        self.assertEqual(len(cache), 0)

        with patch('django.core.cache.cache', cache):
            out = utils.shorten(URL, campaign=1)

        self.assertEqual(out, "/r/testIslug/")
        self.assertEqual(shorts.count(), 1)

        self.assertEqual(len(cache), 1)

        slug = cache['shorturl|initial_redirect||1|cc06be0890c05085b3fbeec2bea1ad9d']
        self.assertEqual(slug, 'testIslug')

    @urandom_patch
    def test_read_db_prefix(self, _mock):
        # This one won't be the latest:
        yesterday = models.ShortenedUrl.objects.create(
            event_type='initial_redirect',
            slug='test-BLUG',
            url=URL,
        )
        yesterday.created = datetime.now() - timedelta(1)
        yesterday.save()

        # This one is just right:
        recently = models.ShortenedUrl.objects.create(
            event_type='initial_redirect',
            slug='test-slug',
            url=URL,
        )
        recently.created = datetime.now() - timedelta(hours=12)
        recently.save()

        # This one's prefix doesn't match:
        models.ShortenedUrl.objects.create(
            event_type='initial_redirect',
            slug='BEST-SLUG',
            url=URL,
        )

        shorts = models.ShortenedUrl.objects.all()
        self.assertEqual(shorts.count(), 3)

        cache = DictCache()
        self.assertEqual(len(cache), 0)

        with patch('django.core.cache.cache', cache):
            out = utils.shorten(URL, prefix='TEST')

        self.assertEqual(out, "/r/test-slug/")
        self.assertEqual(shorts.count(), 3)

        self.assertEqual(len(cache), 1)

        slug = cache['shorturl|initial_redirect|test||cc06be0890c05085b3fbeec2bea1ad9d']
        self.assertEqual(slug, 'test-slug')

    @urandom_patch
    def test_read_db_ignore_prefix(self, _mock):
        # This one is older:
        recently = models.ShortenedUrl.objects.create(
            event_type='initial_redirect',
            slug='testIslug',
            url=URL,
        )
        recently.created = datetime.now() - timedelta(hours=12)
        recently.save()

        # This one is newer but has a prefix:
        models.ShortenedUrl.objects.create(event_type='initial_redirect', slug='test-slug', url=URL)

        shorts = models.ShortenedUrl.objects.all()
        self.assertEqual(shorts.count(), 2)

        cache = DictCache()
        self.assertEqual(len(cache), 0)

        with patch('django.core.cache.cache', cache):
            out = utils.shorten(URL)

        self.assertEqual(out, "/r/testIslug/")
        self.assertEqual(shorts.count(), 2)

        self.assertEqual(len(cache), 1)

        slug = cache['shorturl|initial_redirect|||cc06be0890c05085b3fbeec2bea1ad9d']
        self.assertEqual(slug, 'testIslug')
