from django.test import TestCase

from chapo import models
from chapo.tests import urandom_patch


URL = "http://www.reddit.com/r/food/"


class TestShortenedUrl(TestCase):

    def test_defaults(self):
        """ShortenedUrl requires only url"""
        short = models.ShortenedUrl.objects.create(url=URL)
        self.assertTrue(short.slug)
        self.assertIsNone(short.campaign)
        self.assertEqual(short.url, URL)
        self.assertEqual(short.description, '')
        self.assertEqual(short.event_type, 'generic_redirect')

    @urandom_patch
    def test_slug(self, _mock):
        short = models.ShortenedUrl.objects.create(url=URL)
        self.assertEqual(short.url, URL)
        self.assertEqual(short.slug, 'jSgnUTqptPrV')

    @urandom_patch
    def test_friendly_slug(self, _mock):
        nice_slug = models.ShortenedUrl.make_slug('Healthy Food')
        short = models.ShortenedUrl.objects.create(slug=nice_slug, url=URL)
        self.assertEqual(short.url, URL)
        self.assertEqual(short.slug, 'healthy-food-jSgnUTqp')

    def test_description(self):
        """ShortenedUrl accepts a description"""
        description = "The marketing URL for dem guyz"
        short = models.ShortenedUrl.objects.create(
            url=URL,
            description=description,
        )
        self.assertTrue(short.slug)
        self.assertEqual(short.url, URL)
        self.assertEqual(short.description, description)

    @urandom_patch
    def test_print_pretty(self, _mock):
        """ShortenedUrl prints pretty"""
        short = models.ShortenedUrl.objects.create(url=URL)
        self.assertEqual(unicode(short), u'jSgnUTqptPrV => http://www.reddit.com/r/food/')
        self.assertEqual(str(short), 'jSgnUTqptPrV => http://www.reddit.com/r/food/')
