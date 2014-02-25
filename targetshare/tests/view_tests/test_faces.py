import datetime
import json
import os.path
from decimal import Decimal

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from mock import patch, Mock

from targetshare import models

from .. import EdgeFlipViewTestCase, DATA_PATH, patch_facebook


@patch.dict('django.conf.settings.WEB', mock_subdomain='testserver')
class TestFacesViews(EdgeFlipViewTestCase):

    fixtures = ['test_data']

    def test_faces_get(self):
        ''' Faces endpoint requires POST, so we expect a 405 here '''
        response = self.client.get(reverse('faces'))
        self.assertStatusCode(response, 405)

    @patch_facebook
    def test_faces_initial_entry(self):
        ''' Tests a users first request to the Faces endpoint. We expect to
        receive a JSON response with a status of waiting along with the
        tasks IDs of the Celery jobs we started. We also expect to see an
        extended token saved to Dynamo

        '''
        fbid = self.params['fbid'] = 1111111 # returned by patch
        expires0 = timezone.now() - datetime.timedelta(days=5)
        models.dynamo.Token.items.put_item(
            fbid=fbid,
            appid=self.test_client.fb_app_id,
            token='test-token',
            expires=expires0,
            overwrite=True,
        )
        clientuser = self.test_client.userclients.filter(fbid=fbid)
        self.assertFalse(clientuser.exists())

        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)

        data = json.loads(response.content)
        self.assertTrue(data['px3_task_id'])
        self.assertTrue(data['px4_task_id'])
        refreshed_token = models.dynamo.Token.items.get_item(
            fbid=fbid,
            appid=self.test_client.fb_app_id,
        )
        self.assertGreater(refreshed_token.expires, expires0)
        self.assertTrue(clientuser.exists())

    @patch('targetshare.views.faces.celery')
    def test_faces_px3_wait(self, celery_mock):
        ''' Tests that we receive a JSON status of "waiting" when our px3
        task isn't yet complete
        '''
        self.patch_ranking(celery_mock, px3_ready=False, px4_ready=False)
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid'
        })
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'waiting')

    @patch('targetshare.views.faces.celery')
    def test_faces_px4_wait(self, celery_mock):
        ''' Test that even if px3 is done, we'll wait on px4 if we're not
        ready to give up on it yet
        '''
        self.patch_ranking(celery_mock, px4_ready=False)
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid'
        })
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'waiting')

    @patch('targetshare.views.faces.celery')
    def test_faces_px3_fail(self, celery_mock):
        ''' Test that if px3 fails, we'll return an error even if we're
        still waiting on px4 and not on the last call
        '''
        self.patch_ranking(celery_mock, px3_successful=False, px4_ready=False)
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid'
        })
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertContains(response, 'No friends were identified for you.',
                            status_code=500)

    @patch('targetshare.views.faces.celery')
    def test_faces_px3_fail_px4_success(self, celery_mock):
        """If px3 fails but px4 ranking succeeds, we return an error"""
        self.patch_ranking(celery_mock, px3_successful=False, px4_ready=True)
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid'
        })
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertContains(response, 'No friends were identified for you.',
                            status_code=500)

    @patch('targetshare.views.faces.celery')
    def test_faces_last_call(self, celery_mock):
        ''' Test that gives up on waiting for the px4 result, and serves the
        px3 results
        '''
        self.patch_ranking(celery_mock, px4_ready=False)
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid',
            'last_call': True,
        })
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        assert data['html']

    @patch('targetshare.views.faces.celery')
    def test_faces_complete_crawl(self, celery_mock):
        ''' Test that completes both px3 and px4 crawls '''
        self.patch_ranking(celery_mock)
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid',
            'last_call': True,
        })
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        assert data['html']
        assert models.Event.objects.get(event_type='generated')
        assert models.Event.objects.get(event_type='shown')

    @patch('targetshare.integration.facebook.third_party.requests.get')
    @patch('targetshare.views.faces.celery')
    def test_faces_client_fbobject(self, celery_mock, get_mock):
        self.patch_ranking(celery_mock)
        with open(os.path.join(DATA_PATH, 'gg.html')) as rh:
            get_mock.return_value = Mock(text=rh.read())

        source_url = 'http://somedomain/somepath/'
        campaign_objs = models.CampaignFBObject.objects.filter(source_url=source_url)
        self.assertFalse(campaign_objs.exists())

        self.params.update(
            px3_task_id='dummypx3taskid',
            px4_task_id='dummypx4taskid',
            efobjsrc=source_url,
        )
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')

        # Check second request doesn't hit client site:
        self.assertEqual(get_mock.call_count, 1)
        self.patch_ranking(celery_mock)
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data1 = json.loads(response.content)
        self.assertEqual(data1['status'], 'success')
        self.assertEqual(get_mock.call_count, 1)

        campaign_obj = campaign_objs.get()
        self.assertTrue(campaign_obj.sourced)
        obj_attrs = campaign_obj.fb_object.fbobjectattribute_set.get()
        # Sourced attributes:
        self.assertEqual(obj_attrs.og_title, "Scholarship for Filipino Midwife Student")
        self.assertEqual(obj_attrs.og_description[:22], "The Philippines, like ")
        self.assertEqual(obj_attrs.og_image,
            "https://dpqe0zkrjo0ak.cloudfront.net/pfil/14426/pict_grid7.jpg")
        self.assertEqual(obj_attrs.og_type, 'cause')
        self.assertEqual(obj_attrs.org_name, "GlobalGiving.org")
        # Default attributes:
        self.assertEqual(obj_attrs.og_action, "support")
        self.assertEqual(obj_attrs.page_title, "Support Gun Control")
        self.assertEqual(obj_attrs.sharing_prompt[:25], "Ask your Facebook friends")

        # Check html:
        self.assertIn(obj_attrs.og_image, data['html'])
        self.assertIn(obj_attrs.og_image, data1['html'])

    def test_frame_faces_with_recs(self):
        ''' Tests views.frame_faces '''
        campaign = models.Campaign.objects.get(pk=1)
        client = campaign.client
        fs = models.FacesStyle.objects.create(client=client, name='test')
        models.FacesStyleFiles.objects.create(
            html_template='frame_faces.html', faces_style=fs)
        models.CampaignFacesStyle.objects.create(
            campaign=campaign, faces_style=fs,
            rand_cdf=Decimal('1.000000')
        )
        assert not models.Assignment.objects.exists()
        response = self.client.get(reverse('frame-faces', args=[1, 1]))

        # copied from test_button_with_recs, unclear why this check means success
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response.context['fb_params'],
            {'fb_app_name': 'sharing-social-good', 'fb_app_id': 471727162864364}
        )
        assert models.Assignment.objects.exists()

    def test_frame_faces_encoded(self):
        ''' Testing the views.frame_faces_encoded method '''
        response = self.client.get(
            reverse('frame-faces-encoded', args=['uJ3QkxA4XIk%3D'])
        )
        self.assertStatusCode(response, 200)

    def test_frame_faces(self):
        ''' Testing views.frame_faces '''
        self.assertFalse(models.Event.objects.exists())
        response = self.client.get(reverse('frame-faces', args=[1, 1]))
        client = models.Client.objects.get(campaigns__pk=1)
        campaign = models.Campaign.objects.get(pk=1)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['campaign'], campaign)
        self.assertEqual(
            response.context['content'],
            models.ClientContent.objects.get(pk=1)
        )
        self.assertEqual(
            response.context['fb_params'],
            {
                'fb_app_name': client.fb_app_name,
                'fb_app_id': client.fb_app_id
            }
        )
        properties = response.context['properties']
        campaign_properties = campaign.campaignproperties.get()
        self.assertEqual(properties['client_thanks_url'],
                         self.get_outgoing_url(campaign_properties.client_thanks_url, 1))
        self.assertEqual(properties['client_error_url'],
                         self.get_outgoing_url(campaign_properties.client_error_url, 1))
        assert models.Event.objects.get(event_type='session_start')
        assert models.Event.objects.get(event_type='faces_page_load')
        assert models.Event.objects.get(event_type='faces_iframe_load')

    def test_frame_faces_configurable_urls(self):
        success_url = '//disney.com/'
        error_url = 'http://www.google.com/foo/bar'
        response = self.client.get(reverse('frame-faces', args=[1, 1]), {
            'efsuccessurl': success_url,
            'eferrorurl': error_url,
        })
        self.assertStatusCode(response, 200)
        properties = response.context['properties']
        self.assertEqual(properties['client_thanks_url'],
                         self.get_outgoing_url(success_url, 1))
        self.assertEqual(properties['client_error_url'],
                         self.get_outgoing_url(error_url, 1))

    def test_frame_faces_test_mode_bad_request(self):
        ''' Tests views.frame_faces with test_mode enabled, but without
        providing a test FB ID or Token
        '''
        response = self.client.get(reverse('frame-faces', args=[1, 1]), {
            'secret': settings.TEST_MODE_SECRET,
        })
        self.assertStatusCode(response, 400)

    def test_canvas(self):
        ''' Tests views.canvas '''
        response = self.client.get(reverse('canvas'))
        self.assertStatusCode(response, 200)

    def test_canvas_encoded(self):
        ''' Testing the views.frame_faces_encoded method '''
        self.assertFalse(models.Event.objects.exists())
        response = self.client.get(
            reverse('canvas-faces-encoded', args=['uJ3QkxA4XIk%3D'])
        )
        self.assertStatusCode(response, 200)
        assert models.Event.objects.get(event_type='session_start')
        assert models.Event.objects.get(event_type='faces_page_load')
        assert models.Event.objects.get(event_type='faces_canvas_load')

    def test_canvas_encoded_noslash(self):
        """Encoded canvas endpoint responds with 200 without trailing slash."""
        url = reverse('canvas-faces-encoded', args=['uJ3QkxA4XIk%3D'])
        response = self.client.get(url.rstrip('/'))
        self.assertStatusCode(response, 200)

    def test_faces_email_friends(self):
        ''' Test for the faces_email_friends endpoint '''
        notification = models.Notification.objects.create(
            campaign_id=1, client_content_id=1
        )
        notification_user = models.NotificationUser.objects.create(
            notification=notification, fbid=100, uuid='100',
        )
        prim_user = models.User(
            fbid=100, fname='Primary', lname='User',
            email='primary_user@example.com', gender='male',
            city='Chicago', state='Illinois',
            birthday=timezone.datetime(1984, 1, 1, tzinfo=timezone.utc),
        )
        prim_user.save()
        for x in range(0, 7):
            user = models.User(
                fbid=x,
                fname='Test_%s' % x,
                lname='User_%s' % x,
                email='test+%s@example.com' % x,
                gender='male',
                birthday=timezone.datetime(1984, 1, 1, tzinfo=timezone.utc),
                city='Chicago',
                state='Illinois',
            )
            user.save()
            event_type = 'shown'
            if x > 2:
                event_type = 'generated'
            models.NotificationEvent.objects.create(
                campaign_id=1, client_content_id=1, friend_fbid=x,
                event_type=event_type, notification_user=notification_user
            )

        response = self.client.get(
            reverse('faces-email', args=[notification_user.uuid])
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(
            len(response.context['show_faces']),
            3
        )
        self.assertEqual(
            len(response.context['all_friends']),
            7
        )
        self.assertEqual(
            response.context['user'].fbid,
            100
        )
        self.assertEqual(
            models.Event.objects.filter(event_type='faces_email_page_load').count(),
            1
        )
        self.assertEqual(
            models.Event.objects.filter(event_type='shown').count(),
            3
        )
        self.assertEqual(
            models.Event.objects.filter(event_type='generated').count(),
            4
        )
