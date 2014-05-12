from django import template
from django.test import RequestFactory, TestCase
from mock import patch

from chapo import models
from chapo.tests import urandom_patch


URL = "http://www.reddit.com/r/food/"

chapo_settings = patch('django.conf.settings.CHAPO_SERVER', 'http://edgefl.ip', create=True)


class TestShortUrl(TestCase):

    @chapo_settings
    def test_short_url(self):
        """shorturl returns absolute shortened URL for a ShortenedUrl object"""
        short = models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL)
        out = template.Template(
            "{% load shorturls %}"
            "{% shorturl short %}"
        ).render(template.Context({'short': short}))
        self.assertEqual(out, "http://edgefl.ip/r/ooga-booga/")

    def test_requires_server(self):
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
        self.assertEqual(out, "http://testserver/r/ooga-booga/")

    @chapo_settings
    def test_server(self):
        """shorturl accepts a server argument"""
        short = models.ShortenedUrl.objects.create(slug='ooga-booga', url=URL)
        out = template.Template(
            "{% load shorturls %}"
            "{% shorturl short server='//app.edgeflip.com' %}"
        ).render(template.Context({'short': short}))
        self.assertEqual(out, "//app.edgeflip.com/r/ooga-booga/")

    @chapo_settings
    def test_slug(self):
        """shorturl returns absolute shortened URL for a ShortenedUrl slug"""
        out = template.Template(
            "{% load shorturls %}"
            "{% shorturl slug %}"
        ).render(template.Context({'slug': 'ooga-booga'}))
        self.assertEqual(out, "http://edgefl.ip/r/ooga-booga/")


@urandom_patch
@chapo_settings
class TestShorten(TestCase):

    def test_shorten(self, _mock):
        shorts = models.ShortenedUrl.objects.values('campaign_id', 'event_type', 'slug', 'url')
        self.assertEqual(shorts.count(), 0)
        out = template.Template(
            "{% load shorturls %}"
            "{% shorten 'http://www.english.com/alphabet/a/b/c/d/efgh/' %}"
        ).render(template.Context())
        self.assertEqual(out, "http://edgefl.ip/r/jSgnUTqptPrV/")
        self.assertEqual(shorts.get(), {
            'campaign_id': None,
            'event_type': 'initial_redirect',
            'slug': 'jSgnUTqptPrV',
            'url': 'http://www.english.com/alphabet/a/b/c/d/efgh/',
        })

    def test_prefix(self, _mock):
        shorts = models.ShortenedUrl.objects.values('campaign_id', 'event_type', 'slug', 'url')
        self.assertEqual(shorts.count(), 0)
        out = template.Template(
            "{% load shorturls %}"
            "{% shorten 'http://www.english.com/alphabet/a/b/c/d/efgh/' 'en' %}"
        ).render(template.Context())
        self.assertEqual(out, "http://edgefl.ip/r/en-jSgnUTqpt/")
        self.assertEqual(shorts.get(), {
            'campaign_id': None,
            'event_type': 'initial_redirect',
            'slug': 'en-jSgnUTqpt',
            'url': 'http://www.english.com/alphabet/a/b/c/d/efgh/',
        })
