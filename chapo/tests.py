from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch

from chapo import models


URL = "http://www.reddit.com/r/food/"


class TestShortenedUrl(TestCase):

    def test_defaults(self):
        """ShortenedUrl requires only url"""
        short = models.ShortenedUrl.objects.create(url=URL)
        self.assertTrue(short.slug)
        self.assertEqual(short.url, URL)
        self.assertEqual(short.description, '')

    @patch.object(models, 'urlsafe_b64encode', return_value='foobar43====')
    def test_no_pad_slug(self, _mock):
        """ShortenedUrl.slug is not padded"""
        short = models.ShortenedUrl.objects.create(url=URL)
        self.assertEqual(short.url, URL)
        self.assertEqual(short.slug, 'foobar43')

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

    @patch.object(models, 'urlsafe_b64encode', return_value='foobar43====')
    def test_print_pretty(self, _mock):
        """ShortenedUrl prints pretty"""
        short = models.ShortenedUrl.objects.create(url=URL)
        self.assertEqual(unicode(short), u'foobar43 => http://www.reddit.com/r/food/')
        self.assertEqual(str(short), 'foobar43 => http://www.reddit.com/r/food/')


class TestRedirectService(TestCase):

    def setUp(self):
        self.short = models.ShortenedUrl.objects.create(url=URL)
        self.path = reverse('chapo:main', args=[self.short.slug])

    def test_post(self):
        """el chapo does not accept POSTs"""
        response = self.client.post(self.path)
        self.assertEqual(response.status_code, 405)

    def test_put(self):
        """el chapo does not accept PUTs"""
        response = self.client.put(self.path)
        self.assertEqual(response.status_code, 405)

    def test_delete(self):
        """el chapo does not accept DELETEs"""
        response = self.client.delete(self.path)
        self.assertEqual(response.status_code, 405)

    def test_get_not_found(self):
        """el chapo returns 404s for unknown aliases"""
        self.short.delete()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 404)

    def test_get(self):
        """el chapo returns 301s with content for GETs"""
        response = self.client.get(self.path)
        anchor = """<a href="{0}">{0}</a>""".format(URL)
        self.assertContains(response, anchor, count=1, status_code=301, html=True)
        self.assertEqual(response['Location'], URL)

    def test_head(self):
        """el chapo returns 301s without content for HEADs"""
        response = self.client.head(self.path)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.content, '')
        self.assertEqual(response['Location'], URL)
