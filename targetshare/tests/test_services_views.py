import json
import urllib

from django.core.urlresolvers import reverse
from mock import patch

from targetshare import models
from targetshare.utils import encodeDES

from . import EdgeFlipViewTestCase


@patch.dict('django.conf.settings.WEB', mock_subdomain='testserver')
class TestServicesViews(EdgeFlipViewTestCase):

    fixtures = ['test_data']

    @patch('targetshare.views.services.facebook.client')
    def test_health_check(self, fb_mock):
        ''' Tests views.health_check '''
        fb_mock.urlload.return_value = {'id': 6963}
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

    def test_outgoing_url_missing_protocol(self):
        url = 'www.badeggs.com'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id,
                                               urllib.quote_plus(url)])
        response = self.client.get(redirector)
        self.assertStatusCode(response, 302)
        self.assertEqual(response['Location'], "http://{}".format(url))

    def test_outgoing_url_implicit_protocol(self):
        url = '//www.badeggs.com'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id,
                                               urllib.quote_plus(url)])
        response = self.client.get(redirector)
        self.assertStatusCode(response, 302)
        self.assertEqual(response['Location'], "http:{}".format(url))

    def test_outgoing_url_only_path(self):
        url = '/weird'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id,
                                               urllib.quote_plus(url)])
        response = self.client.get(redirector)
        self.assertStatusCode(response, 302)
        self.assertEqual(response['Location'], "http://testserver{}".format(url))

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

    def test_incoming_url_redirect(self):
        response = self.client.get(
            reverse('incoming-encoded', args=[
                encodeDES('1/1')])
        )
        self.assertStatusCode(response, 302)
        self.assertTrue(
            models.Event.objects.filter(event_type='incoming_redirect').exists()
        )
        self.assertEqual(
            response['Location'],
            'http://local.edgeflip.com:8080/mocks/guncontrol_share?efcmpgslug=t0AGY7FMXjM%3D'
        )

    def test_incoming_url_redirect_fb_auth_declined(self):
        events = models.Event.objects.filter(event_type='auth_fail')
        self.assertFalse(events.exists())

        response = self.client.get(
            reverse('incoming-encoded', args=[encodeDES('1/1')]),
            {'error': 'access_denied', 'error_reason': 'user_denied'}
        )
        campaign_props = models.CampaignProperties.objects.get(campaign__pk=1)
        self.assertStatusCode(response, 302)
        expected_url = 'http://testserver{}?{}'.format(
            reverse('outgoing', args=[
                campaign_props.campaign.client.fb_app_id,
                urllib.quote_plus(campaign_props.client_error_url)]
            ),
            urllib.urlencode({'campaignid': campaign_props.campaign.pk})
        )
        self.assertEqual(response['Location'], expected_url)

        event = events.get()
        self.assertEqual(event.content, 'oauth')
