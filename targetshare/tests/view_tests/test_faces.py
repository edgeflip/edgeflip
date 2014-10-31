import datetime
import json
import os.path

from django.conf import settings
from django.core.urlresolvers import resolve, reverse
from django.test import RequestFactory
from django.utils import timezone
from django.utils.importlib import import_module
from mock import patch, Mock

from targetshare import models

from .. import EdgeFlipViewTestCase, DATA_PATH, patch_facebook


@patch('targetshare.views.faces.celery')
class TestFaces(EdgeFlipViewTestCase):

    fixtures = ['test_data']

    task_key = 'faces_tasks_px_1_1_1'
    task_ids = ('dummypx3taskid', 'dummypx4taskid')

    @classmethod
    def setUpClass(cls):
        super(TestFaces, cls).setUpClass()
        cls.session_engine = import_module(settings.SESSION_ENGINE)

    def setUp(self):
        super(TestFaces, self).setUp()
        self.factory = RequestFactory()

    # Helpers for minute control of requests #

    def post_request(self, data=(), **extra):
        cookie = self.factory.cookies.get(settings.SESSION_COOKIE_NAME, None)
        session_key = cookie and cookie.value
        request = self.factory.post(reverse('faces'), data, **extra)
        request.session = self.session_engine.SessionStore(session_key)
        return request

    def get_response(self, request):
        match = resolve(request.path)
        self.factory.cookies[settings.SESSION_COOKIE_NAME] = request.session.session_key
        return match.func(request, *match.args, **match.kwargs)

    # Tests #

    def test_get(self, _celery_mock):
        """Response to GET is code 405"""
        response = self.client.get(reverse('faces'))
        self.assertStatusCode(response, 405)

    @patch_facebook
    def test_initial_entry(self, celery_mock):
        """Initial request initiates tasks and extends token"""
        fbid = self.params['fbid'] = 1111111 # returned by patch

        expires0 = timezone.now() - datetime.timedelta(days=5)
        models.dynamo.Token.items.put_item(
            fbid=fbid,
            appid=self.test_client.fb_app_id,
            token='test-token',
            expires=expires0,
        )
        clientuser = self.test_client.userclients.filter(fbid=fbid)
        self.assertFalse(clientuser.exists())

        request = self.post_request(self.params)
        response = self.get_response(request)
        self.assertStatusCode(response, 200)

        data = json.loads(response.content)
        self.assertEqual(data['campaignid'], 1)
        self.assertEqual(data['contentid'], 1)

        task_ids = request.session['faces_tasks_px_1111111_1_1']
        self.assertEqual(len(task_ids), 2)

        refreshed_token = models.dynamo.Token.items.get_item(
            fbid=fbid,
            appid=self.test_client.fb_app_id,
        )
        self.assertGreater(refreshed_token.expires, expires0)
        self.assertTrue(clientuser.exists())

    def test_px3_wait(self, celery_mock):
        """Receive "waiting" response when px3 task incomplete"""
        self.patch_targeting(celery_mock, px3_ready=False, px4_ready=False)
        request = self.post_request(self.params)
        request.session[self.task_key] = self.task_ids

        response = self.get_response(request)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'waiting')
        self.assertEqual(request.session[self.task_key], self.task_ids)
        self.assertEqual(len(request.session.keys()), 1)

    def test_px4_wait(self, celery_mock):
        """Receive "waiting" response when px3 task complete but px4 incomplete"""
        self.patch_targeting(celery_mock, px4_ready=False)
        request = self.post_request(self.params)
        request.session[self.task_key] = self.task_ids

        response = self.get_response(request)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'waiting')
        self.assertEqual(request.session[self.task_key], self.task_ids)
        self.assertEqual(len(request.session.keys()), 1)

    def test_px3_fail(self, celery_mock):
        """Receive error response as soon as px3 task fails"""
        self.patch_targeting(celery_mock, px3_successful=False, px4_ready=False)
        request = self.post_request(self.params)
        request.session[self.task_key] = self.task_ids
        response = self.get_response(request)
        self.assertContains(response, 'No friends were identified for you.', status_code=500)

    def test_px3_fail_px4_success(self, celery_mock):
        """Receive error response px3 task fails despite px4 success"""
        self.patch_targeting(celery_mock, px3_successful=False, px4_ready=True)
        request = self.post_request(self.params)
        request.session[self.task_key] = self.task_ids
        response = self.get_response(request)
        self.assertContains(response, 'No friends were identified for you.', status_code=500)

    def test_last_call(self, celery_mock):
        """Receive px3 results on last call if px4 not ready"""
        self.patch_targeting(celery_mock, px4_ready=False)
        request = self.post_request(dict(self.params, last_call=True))
        request.session[self.task_key] = self.task_ids
        response = self.get_response(request)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        assert data['html']

    @patch('targetshare.views.faces.LOG_RVN')
    def test_px3_fail_last_call(self, logger_mock, celery_mock):
        """Receive 503 response to last call request if there are no results"""
        self.patch_targeting(celery_mock, px3_ready=False, px4_ready=False)
        request = self.post_request(dict(self.params, last_call=True))
        request.session[self.task_key] = self.task_ids
        response = self.get_response(request)
        self.assertContains(response, 'Response has taken too long, giving up', status_code=503)
        self.assertIn('px3 failed to complete', logger_mock.fatal.call_args[0][0])

    def test_px4_filtering(self, celery_mock):
        self.test_edge = self.test_edge._replace(px3_score=1.0, px4_score=1.5)
        self.patch_targeting(celery_mock, px4_filtering=True)
        request = self.post_request(self.params)
        request.session[self.task_key] = self.task_ids
        response = self.get_response(request)
        self.assertStatusCode(response, 200)

        generated = request.visit.events.get(event_type='generated')
        shown = request.visit.events.get(event_type='shown')
        self.assertEqual(generated.content, 'px3_score: 1.0 (123), px4_score: 1.5 (1234)')
        self.assertEqual(shown.content, 'px4_score: 1.5 (1234)')

    def test_complete_crawl(self, celery_mock):
        ''' Test that completes both px3 and px4 crawls '''
        self.test_edge = self.test_edge._replace(px3_score=1.0, px4_score=1.5)
        self.patch_targeting(celery_mock)
        request = self.post_request(self.params)
        request.session[self.task_key] = self.task_ids
        response = self.get_response(request)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['html'])
        generated = request.visit.events.get(event_type='generated')
        shown = request.visit.events.get(event_type='shown')
        self.assertEqual(generated.content, 'px3_score: 1.0 (123), px4_score: 1.5 (1234)')
        self.assertEqual(shown.content, 'px4_score: 1.5 (1234)')

    def test_reload(self, celery_mock):
        self.test_edge = self.test_edge._replace(px3_score=1.0, px4_score=1.5)

        self.patch_targeting(celery_mock)
        request = self.post_request(self.params)
        request.session[self.task_key] = self.task_ids
        request.session.save()
        response = self.get_response(request)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['html'])

        events = request.visit.events.all()
        generated0 = events.filter(event_type='generated').count()
        shown0 = events.filter(event_type='shown').count()
        self.assertEqual(shown0, 1)
        self.assertEqual(generated0, 1)

        self.patch_targeting(celery_mock)
        request = self.post_request(self.params)
        response = self.get_response(request)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['html'])

        generated1 = events.filter(event_type='generated').count()
        shown1 = events.filter(event_type='shown').count()
        self.assertEqual(shown1, shown0 * 2)
        self.assertEqual(generated1, generated0)

    def test_session_exclusion(self, celery_mock):
        self.test_edge = self.test_edge._replace(px3_score=1.0, px4_score=1.5)

        self.patch_targeting(celery_mock)
        request = self.post_request(self.params)
        request.session[self.task_key] = self.task_ids
        request.session['face_exclusions_1_1_1'] = [1]
        request.session.save()
        response = self.get_response(request)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['html'])

        events = request.visit.events.all()
        generated0 = events.filter(event_type='generated').count()
        shown0 = events.filter(event_type='shown').count()
        self.assertEqual(shown0, 0)
        self.assertEqual(generated0, 1)

    @patch('targetshare.integration.facebook.third_party.requests.get')
    def test_client_fbobject(self, get_mock, celery_mock):
        with open(os.path.join(DATA_PATH, 'gg.html')) as rh:
            get_mock.return_value = Mock(text=rh.read())

        source_url = 'http://somedomain/somepath/'
        self.params['efobjsrc'] = source_url
        campaign_objs = models.CampaignFBObject.objects.filter(source_url=source_url)
        self.assertFalse(campaign_objs.exists())

        self.patch_targeting(celery_mock)
        request = self.post_request(self.params)
        request.session[self.task_key] = self.task_ids
        request.session.save()
        response = self.get_response(request)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')

        # Assert second request doesn't hit client site:
        self.assertEqual(get_mock.call_count, 1)
        self.patch_targeting(celery_mock)
        request = self.post_request(self.params)
        response = self.get_response(request)
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


class TestFrameFaces(EdgeFlipViewTestCase):

    fixtures = ['test_data']

    def test_with_recs(self):
        """frame_faces respects page styles"""
        campaign = models.Campaign.objects.get(pk=1)
        campaign_page_style_set = campaign.campaignpagestylesets.get(
            page_style_set__page_styles__page=models.Page.objects.get_frame_faces(),
        )
        page_style = campaign_page_style_set.page_style_set.page_styles.get()

        self.assertFalse(models.Assignment.objects.exists())
        response = self.client.get(reverse('frame-faces', args=[1, 1]))

        url = '//assets-edgeflip.s3.amazonaws.com/s/c/edgeflip-base-0.css'
        self.assertEqual(page_style.url, url)
        link_html = '<link rel="stylesheet" type="text/css" href="{}" />'.format(url)
        self.assertContains(response, link_html, count=1, html=True)

        assignment = models.Assignment.objects.get(feature_type='page_style_set_id')
        self.assertEqual(assignment.feature_row, campaign_page_style_set.page_style_set_id)

    def test_encoded(self):
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

    def test_configurable_urls(self):
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

    def test_test_mode(self):
        response = self.client.get(reverse('frame-faces', args=[1, 1]), {
            'secret': settings.TEST_MODE_SECRET,
            'fbid': 1234,
            'token': 'boo-urns',
        })
        self.assertStatusCode(response, 200)
        test_mode = response.context['test_mode']
        self.assertTrue(test_mode)
        self.assertEqual(test_mode.fbid, 1234)
        self.assertEqual(test_mode.token, 'boo-urns')

    def test_test_mode_bad_secret(self):
        response = self.client.get(reverse('frame-faces', args=[1, 1]), {
            'secret': settings.TEST_MODE_SECRET[:4] + 'oops',
            'fbid': 1234,
            'token': 'oops',
        })
        self.assertStatusCode(response, 200)
        test_mode = response.context['test_mode']
        self.assertFalse(test_mode)
        self.assertIsNone(test_mode.fbid)
        self.assertIsNone(test_mode.token)

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

    def test_email_friends(self):
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

        response = self.client.get(reverse('faces-email', args=[notification_user.uuid]))
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['show_faces']), 3)
        self.assertEqual(len(response.context['all_friends']), 7)
        self.assertEqual(response.context['user'].fbid, 100)
        self.assertEqual(models.Event.objects.filter(event_type='faces_email_page_load').count(), 1)
        self.assertEqual(models.Event.objects.filter(event_type='shown').count(), 3)
        self.assertEqual(models.Event.objects.filter(event_type='generated').count(), 4)
