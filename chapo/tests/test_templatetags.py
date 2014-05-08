from django import template
from django.test import RequestFactory, TestCase
from mock import patch

from targetshare.models.relational import Client

from chapo import models
from chapo.tests import urandom_patch, BYTES, BYTES2


URL = "http://www.reddit.com/r/food/"

chapo_settings = patch('django.conf.settings.CHAPO_REDIRECTOR_DOMAIN', 'edgefl.ip', create=True)


class DictCache(dict):

    __slots__ = ()

    def set(self, key, value, timeout=None):
        self[key] = value


class TestShortUrl(TestCase):

    @chapo_settings
    def test_short_url(self):
        """shorturl returns absolute shortened URL for a ShortenedUrl object"""
        short = models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL)
        out = template.Template(
            "{% load shorturls %}"
            "{% shorturl short %}"
        ).render(template.Context({'short': short}))
        self.assertEqual(out, "//edgefl.ip/r/ooga-booga/")

    def test_requires_domain(self):
        """shorturl requires global setting or request in context"""
        short = models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL)
        with self.assertRaises(KeyError):
            template.Template(
                "{% load shorturls %}"
                "{% shorturl short %}"
            ).render(template.Context({'short': short}))

    def test_request_domain(self):
        """shorturl falls back to request domain"""
        request_factory = RequestFactory()
        context = template.Context({
            'request': request_factory.get('/fuzz/'),
            'short': models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL),
        })
        out = template.Template(
            "{% load shorturls %}"
            "{% shorturl short %}"
        ).render(context)
        self.assertEqual(out, "//testserver/r/ooga-booga/")

    @chapo_settings
    def test_protocol(self):
        """shorturl accepts a protocol"""
        short = models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL)
        out = template.Template(
            "{% load shorturls %}"
            "{% shorturl short protocol='ssh:' %}"
        ).render(template.Context({'short': short}))
        self.assertEqual(out, "ssh://edgefl.ip/r/ooga-booga/")

    @chapo_settings
    def test_slug(self):
        """shorturl returns absolute shortened URL for a ShortenedUrl slug"""
        out = template.Template(
            "{% load shorturls %}"
            "{% shorturl slug %}"
        ).render(template.Context({'slug': 'ooga-booga'}))
        self.assertEqual(out, "//edgefl.ip/r/ooga-booga/")


@chapo_settings
class TestShorten(TestCase):

    @urandom_patch
    def test_shorten(self, _mock):
        shorts = models.ShortenedUrl.objects.values('campaign_id', 'event_type', 'slug', 'url')
        self.assertEqual(shorts.count(), 0)
        out = template.Template(
            "{% load shorturls %}"
            "{% shorten 'http://www.english.com/alphabet/a/b/c/d/efgh/' %}"
        ).render(template.Context())
        self.assertEqual(out, "//edgefl.ip/r/jSgnUTqptPrV/")
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
        out = template.Template(
            "{% load shorturls %}"
            "{% shorten 'http://www.english.com/alphabet/a/b/c/d/efgh/' 'en' %}"
        ).render(template.Context())
        self.assertEqual(out, "//edgefl.ip/r/en-jSgnUTqpt/")
        self.assertEqual(shorts.get(), {
            'campaign_id': None,
            'event_type': 'initial_redirect',
            'slug': 'en-jSgnUTqpt',
            'url': 'http://www.english.com/alphabet/a/b/c/d/efgh/',
        })

    @patch('os.urandom', side_effect=(BYTES, BYTES, BYTES2))
    @patch('chapo.templatetags.shorturls.LOG')
    def test_retry(self, log_mock, _urandom_mock):
        models.ShortenedUrl.objects.create(url=URL) # pre-existing
        shorts = models.ShortenedUrl.objects.values('campaign_id', 'event_type', 'slug', 'url')
        self.assertEqual(shorts.count(), 1)

        out = template.Template(
            "{% load shorturls %}"
            "{% shorten 'http://www.english.com/alphabet/a/b/c/d/efgh/' %}"
        ).render(template.Context())
        self.assertEqual(out, "//edgefl.ip/r/WSTUhHUshgrt/")

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
        out = template.Template(
            "{% load shorturls %}"
            "{% shorten 'http://www.reddit.com/r/food/' %}"
        ).render(template.Context())
        self.assertEqual(out, "//edgefl.ip/r/jSgnUTqptPrV/")
        self.assertEqual(shorts.count(), 0)

    @urandom_patch
    @patch('django.core.cache.cache',
           {'shorturl|initial_redirect|food||cc06be0890c05085b3fbeec2bea1ad9d': 'food-jSgnUTqp'})
    def test_cache_prefix(self, _urandom_mock):
        """shorten checks cache for existing ShortenedUrl slug and respects prefix"""
        shorts = models.ShortenedUrl.objects.all()
        self.assertEqual(shorts.count(), 0)
        out = template.Template(
            "{% load shorturls %}"
            "{% shorten 'http://www.reddit.com/r/food/' 'food' %}"
        ).render(template.Context())
        self.assertEqual(out, "//edgefl.ip/r/food-jSgnUTqp/")
        self.assertEqual(shorts.count(), 0)

    @urandom_patch
    @patch('django.core.cache.cache',
           {'shorturl|initial_redirect||1|cc06be0890c05085b3fbeec2bea1ad9d': 'jSgnUTqptPrV'})
    def test_cache_campaign_id(self, _urandom_mock):
        """shorten checks cache for existing ShortenedUrl slug and respects campaign ID"""
        shorts = models.ShortenedUrl.objects.all()
        self.assertEqual(shorts.count(), 0)
        out = template.Template(
            "{% load shorturls %}"
            "{% shorten 'http://www.reddit.com/r/food/' campaign=1 %}"
        ).render(template.Context())
        self.assertEqual(out, "//edgefl.ip/r/jSgnUTqptPrV/")
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
        out = template.Template(
            "{% load shorturls %}"
            "{% shorten 'http://www.reddit.com/r/food/' campaign=campaign %}"
        ).render(template.Context({'campaign': campaign}))
        self.assertEqual(out, "//edgefl.ip/r/jSgnUTqptPrV/")
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
            out = template.Template(
                "{% load shorturls %}"
                "{% shorten 'http://www.reddit.com/r/food/' 'food' campaign %}"
            ).render(template.Context({'campaign': campaign}))

        self.assertEqual(out, "//edgefl.ip/r/food-jSgnUTqp/")
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
