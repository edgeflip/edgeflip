from django import template
from django.test import RequestFactory, TestCase
from mock import patch

from chapo import models
from chapo.tests import urandom_patch, BYTES, BYTES2


URL = "http://www.reddit.com/r/food/"

chapo_settings = patch('django.conf.settings.CHAPO_REDIRECTOR_DOMAIN', 'edgefl.ip', create=True)


class TestShortUrlsTemplateTags(TestCase):

    @chapo_settings
    def test_short_url(self):
        """shorturl returns absolute shortened URL for a ShortenedUrl object"""
        short = models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL)
        out = template.Template(
            "{% load shorturls %}"
            "{% shorturl short %}"
        ).render(template.Context({'short': short}))
        self.assertEqual(out, "//edgefl.ip/r/ooga-booga/")

    def test_short_url_requires_domain(self):
        """shorturl requires global setting or request in context"""
        short = models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL)
        with self.assertRaises(KeyError):
            template.Template(
                "{% load shorturls %}"
                "{% shorturl short %}"
            ).render(template.Context({'short': short}))

    def test_short_url_request_domain(self):
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
    def test_short_url_protocol(self):
        """shorturl accepts a protocol"""
        short = models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL)
        out = template.Template(
            "{% load shorturls %}"
            "{% shorturl short protocol='ssh:' %}"
        ).render(template.Context({'short': short}))
        self.assertEqual(out, "ssh://edgefl.ip/r/ooga-booga/")

    @urandom_patch
    @chapo_settings
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
    @chapo_settings
    def test_shorten_prefix(self, _mock):
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
    @chapo_settings
    def test_shorten_retry(self, log_mock, _urandom_mock):
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
