from django.core.urlresolvers import reverse
from django.test import TestCase

from targetshare.models import relational

from chapo import models


URL = "http://www.reddit.com/r/food/"


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
