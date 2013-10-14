import json
import urllib

from django.core.urlresolvers import reverse
from mock import patch

from targetshare import models

from . import EdgeFlipViewTestCase


@patch.dict('django.conf.settings.WEB', mock_subdomain='testserver')
class TestServicesViews(EdgeFlipViewTestCase):

    fixtures = ['test_data']

    @patch('targetshare.views.services.facebook.client')
    def test_health_check(self, fb_mock):
        ''' Tests views.health_check '''
        fb_mock.getUrlFb.return_value = {'id': 6963}
        response = self.client.get(reverse('health-check'))
        self.assertStatusCode(response, 200)
        self.assertEqual(json.loads(response.content), {
            'database': True,
            'facebook': True,
            'dynamo': True,
        })

    def test_health_check_elb(self):
        ''' Test health-check view from Amazon ELB perspective '''
        response = self.client.get(reverse('health-check'), {'elb': True})
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, "It's Alive!")

    def test_outgoing_url(self):
        url = 'http://www.google.com/path?query=string&string=query'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id,
                                               urllib.quote_plus(url)])
        response = self.client.get(redirector)
        self.assertStatusCode(response, 302)
        self.assertEqual(response['Location'], url)

        visit = models.Visit.objects.get(session_id=self.client.session.session_key)
        self.assertEqual(visit.events.count(), 2)
        self.assertEqual(set(visit.events.values_list('event_type', flat=True)),
                         {'session_start', 'outgoing_redirect'})
        event = visit.events.get(event_type='outgoing_redirect')
        self.assertEqual(event.content, url)

    def test_outgoing_url_bad_source(self):
        url = 'http://www.google.com/path?query=string&string=query'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id,
                                               urllib.quote_plus(url)])
        response = self.client.get(redirector, {'source': 'true!!1!'})
        self.assertContains(response, 'Invalid "source" flag', status_code=400)

    def test_outgoing_url_bad_campaign(self):
        url = 'http://www.google.com/path?query=string&string=query'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id,
                                               urllib.quote_plus(url)])
        response = self.client.get(redirector, {'source': '1', 'campaignid': 'two'})
        self.assertContains(response, 'Invalid campaign identifier', status_code=400)

    def test_outgoing_url_missing_campaign(self):
        url = 'http://www.google.com/path?query=string&string=query'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id,
                                               urllib.quote_plus(url)])
        self.assertFalse(models.Campaign.objects.filter(pk=9999).exists())
        response = self.client.get(redirector, {'source': '1', 'campaignid': '9999'})
        self.assertStatusCode(response, 404)

    def test_outgoing_url_source(self):
        url = 'http://www.google.com/path?query=string&string=query'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id,
                                               urllib.quote_plus(url)])
        campaign = models.Campaign.objects.all()[0]
        final_url = url + '&rs=ef{}'.format(campaign.pk)

        response = self.client.get(redirector, {'campaignid': campaign.pk})
        self.assertStatusCode(response, 302)
        self.assertEqual(response['Location'], final_url)

        visit = models.Visit.objects.get(session_id=self.client.session.session_key)
        self.assertEqual(visit.events.count(), 2)
        self.assertEqual(set(visit.events.values_list('event_type', flat=True)),
                         {'session_start', 'outgoing_redirect'})
        event = visit.events.get(event_type='outgoing_redirect')
        self.assertEqual(event.content, final_url)
