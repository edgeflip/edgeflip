import json
import urllib

from django.core.urlresolvers import reverse
from mock import Mock, patch

from core.utils import encryptedslug

from targetshare import models

from .. import EdgeFlipViewTestCase, patch_facebook


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

    @patch_facebook(min_friends=1, max_friends=25)
    def test_health_check_faces(self):
        ''' Test Faces health-check view '''
        response = self.client.get(reverse('faces-health-check'), {
            'api': '1.0',
            'fbid': 1,
            'token': 'token_str',
            'num_face': 9,
            'campaign': 1,
            'content': 1
        })
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp['status'], 'SUCCESS')

    def test_health_check_faces_bad_request(self):
        ''' Test Faces health-check view with bad request '''
        response = self.client.get(reverse('faces-health-check'), {
            'api': '1.0',
            'fbid': 1,
            'token': 'token_str',
            'campaign': 1,
            'content': 1
        })
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['num_face'][0], 'This field is required.')

    @patch('targetshare.tasks.targeting.proximity_rank_four')
    @patch('targetshare.tasks.targeting.proximity_rank_three')
    def test_health_check_faces_failure(self, px3_mock, px4_mock):
        px3_mock.delay.return_value = Mock(status='FAILURE', id='1-1')
        px4_mock.delay.return_value = Mock(status='FAILURE', id='1-2')
        response = self.client.get(reverse('faces-health-check'), {
            'api': '1.0',
            'fbid': 1,
            'token': 'token_str',
            'num_face': 9,
            'campaign': 1,
            'content': 1
        })
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp['status'], 'FAILURE')
        self.assertEqual(resp['px3_status'], 'FAILURE')
        self.assertEqual(resp['px4_status'], 'FAILURE')

    def test_outgoing_url(self):
        url = 'http://www.google.com/path?query=string&string=query'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id, url])
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
                                               url])
        response = self.client.get(redirector, {'source': 'true!!1!'})
        self.assertContains(response, 'Invalid "source" flag', status_code=400)

    def test_outgoing_url_bad_campaign(self):
        url = 'http://www.google.com/path?query=string&string=query'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id,
                                               url])
        response = self.client.get(redirector, {'source': '1', 'campaignid': 'two'})
        self.assertContains(response, 'Invalid campaign identifier', status_code=400)

    def test_outgoing_url_missing_campaign(self):
        url = 'http://www.google.com/path?query=string&string=query'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id,
                                               url])
        self.assertFalse(models.Campaign.objects.filter(pk=9999).exists())
        response = self.client.get(redirector, {'source': '1', 'campaignid': '9999'})
        self.assertStatusCode(response, 404)

    def test_outgoing_url_missing_protocol(self):
        url = 'www.badeggs.com'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id,
                                               url])
        response = self.client.get(redirector)
        self.assertStatusCode(response, 302)
        self.assertEqual(response['Location'], "http://{}".format(url))

    def test_outgoing_url_implicit_protocol(self):
        url = '//www.badeggs.com'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id, url])
        response = self.client.get(redirector)
        self.assertStatusCode(response, 302)
        self.assertEqual(response['Location'], "http:{}".format(url))

    def test_outgoing_url_only_path(self):
        url = '/weird'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id, url])
        response = self.client.get(redirector)
        self.assertStatusCode(response, 302)
        self.assertEqual(response['Location'], "http://testserver{}".format(url))

    def test_outgoing_url_source(self):
        url = 'http://www.google.com/path?query=string&string=query'
        redirector = reverse('outgoing', args=[self.test_client.fb_app_id, url])
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
        self.assertEqual(event.campaign, campaign)

    @patch('targetshare.views.services.store_oauth_token')
    def test_incoming_url_redirect(self, task_mock):
        campaign = models.Campaign.objects.get(pk=1)
        response = self.client.get(
            reverse('incoming-encoded', args=[encryptedslug.make_slug(campaign, 1)])
        )
        self.assertStatusCode(response, 302)
        self.assertTrue(
            models.Event.objects.filter(event_type='incoming_redirect').exists()
        )
        self.assertEqual(
            response['Location'],
            'http://local.edgeflip.com:8080/mocks/guncontrol_share?efcmpgslug=uV8JNec7DxI'
        )
        self.assertEqual(encryptedslug.get_params('uV8JNec7DxI'), (1, 1, 1))
        self.assertFalse(task_mock.delay.called)

    def test_incoming_url_redirect_fb_auth_declined(self):
        auth_fails = models.Event.objects.filter(event_type='auth_fail')
        redirects = models.Event.objects.filter(event_type='incoming_redirect')
        self.assertFalse(auth_fails.exists())
        self.assertFalse(redirects.exists())

        campaign = models.Campaign.objects.get(pk=1)
        response = self.client.get(
            reverse('incoming-encoded', args=[encryptedslug.make_slug(campaign, 1)]),
            {'error': 'access_denied', 'error_reason': 'user_denied'}
        )
        self.assertStatusCode(response, 302)

        campaign_props = campaign.campaignproperties.get()
        outgoing_path = reverse('outgoing', args=[
            campaign_props.campaign.client.fb_app_id,
            campaign_props.client_error_url]
        )
        outgoing_url = "{}?{}".format(outgoing_path, urllib.urlencode({
            'campaignid': campaign_props.campaign.pk,
        }))
        expected_url = 'http://testserver' + outgoing_url
        self.assertEqual(response['Location'], expected_url)

        session_id = self.client.cookies['sessionid'].value
        visit = models.Visit.objects.get(
            session_id=session_id,
            app_id=campaign_props.campaign.client.fb_app_id,
        )

        auth_fail = auth_fails.get()
        self.assertEqual(auth_fail.content, 'oauth')
        self.assertEqual(auth_fail.visit_id, visit.visit_id)
        self.assertEqual(auth_fail.campaign_id, 1)
        self.assertEqual(auth_fail.client_content_id, 1)

        incoming = redirects.get()
        self.assertEqual(incoming.content, outgoing_url)
        self.assertEqual(incoming.visit_id, visit.visit_id)
        self.assertEqual(incoming.campaign_id, 1)
        self.assertEqual(incoming.client_content_id, 1)

    @patch('targetshare.views.services.store_oauth_token')
    def test_incoming_url_fb_auth_permitted(self, task_mock):
        async_result = task_mock.delay.return_value
        async_result.id = async_result.task_id = 'OAUTH_TOKEN_TASK-1'
        campaign = models.Campaign.objects.get(pk=1)
        path = reverse('incoming-encoded', args=[encryptedslug.make_slug(campaign, 1)])
        response = self.client.get(path, {'code': 'PIEZ'})
        self.assertStatusCode(response, 302)
        self.assertNotIn('code=', response['Location'])
        session = self.client.session
        self.assertEqual(session['oauth_task'], 'OAUTH_TOKEN_TASK-1')
        visit_id = models.Visit.objects.only('visit_id').get(session_id=session.session_key).visit_id
        task_mock.delay.assert_called_once_with(1, 'PIEZ', 'http://testserver' + path,
                                                visit_id=visit_id, campaign_id=1, content_id=1)
