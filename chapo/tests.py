from django import template
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase
from mock import patch

from targetshare.models import relational

from chapo import models


URL = "http://www.reddit.com/r/food/"

BYTES = '\xad\xe0\xd0\x9a\xf5\xe1\xedz\xe9\xd9\xd2\x8b'
BYTES2 = '\x08A\x1av\xbfH\xfaK{\x1e\xd2n'
urandom_patch = patch('os.urandom', return_value=BYTES)

chapo_settings = patch('django.conf.settings.CHAPO_REDIRECTOR_DOMAIN', 'edgefl.ip', create=True)

settings_patch = patch('django.conf.settings.CELERY_ALWAYS_EAGER', True)


def setup_module():
    settings_patch.start()


def teardown_module():
    settings_patch.stop()


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


class TestRedirectEvent(TestCase):

    fixtures = ('test_data',)

    def setUp(self):
        self.campaign = relational.Campaign.objects.all()[0]
        self.short = self.campaign.shortenedurls.create(event_type='initial_redirect', url=URL)
        self.path = reverse('chapo:main', args=[self.short.slug])

    def test_event(self):
        """el chapo records an event"""
        events = relational.Event.objects.all()
        visits = relational.Visit.objects.all()

        self.assertEqual(events.count(), 0)
        self.assertEqual(visits.count(), 0)

        response = self.client.get(self.path)

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], URL)

        visit = visits.get()
        event_values = events.values('event_type', 'campaign_id', 'client_content',
                                     'content', 'friend_fbid', 'activity_id')

        self.assertEqual(visit.session_id, self.client.cookies['sessionid'].value)
        self.assertEqual({event.visit for event in events}, {visit})
        self.assertEqual({event.event_type for event in events},
                         {'session_start', 'initial_redirect'})
        self.assertEqual(event_values.get(event_type='initial_redirect'), {
            'event_type': 'initial_redirect',
            'campaign_id': self.campaign.pk,
            'client_content': None,
            'content': self.short.slug,
            'friend_fbid': None,
            'activity_id': None,
        })


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
