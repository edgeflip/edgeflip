import datetime
import json
import os.path
import re
import urllib
from decimal import Decimal

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from django.utils import timezone
from django.utils.importlib import import_module
from mock import patch, Mock

from targetshare import models
from targetshare.views import _get_visit

from . import EdgeFlipTestCase


DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


class TestVisit(EdgeFlipTestCase):

    @classmethod
    def setUpClass(cls):
        cls.session_engine = import_module(settings.SESSION_ENGINE)

    def setUp(self):
        super(TestVisit, self).setUp()
        self.factory = RequestFactory()

    def get_request(self, path='/'):
        cookie = self.factory.cookies.get(settings.SESSION_COOKIE_NAME, None)
        session_key = cookie and cookie.value
        request = self.factory.get(path)
        request.session = self.session_engine.SessionStore(session_key)
        return request

    def test_new_visit(self):
        visit = _get_visit(self.get_request(), 1)
        self.assertTrue(visit.session_id)
        self.assertEqual(visit.app_id, 1)
        start_event = visit.events.get()
        self.assertEqual(start_event.event_type, 'session_start')

    def test_update_visit(self):
        visit = _get_visit(self.get_request(), 1)
        session_id = visit.session_id
        self.assertTrue(session_id)
        self.assertIsNone(visit.fbid)

        self.factory.cookies[settings.SESSION_COOKIE_NAME] = session_id
        visit = _get_visit(self.get_request(), 1, fbid=9)
        self.assertEqual(visit.session_id, session_id)
        self.assertEqual(visit.fbid, 9)

    def test_visit_expiration(self):
        request0 = self.get_request()
        visit0 = _get_visit(request0, 1)
        session_id0 = visit0.session_id
        self.assertTrue(session_id0)

        # Make session old:
        session0 = Session.objects.get(session_key=session_id0)
        session0.expire_date = datetime.datetime(1, 1, 1, 0, 0, tzinfo=timezone.utc)
        session0.save()

        self.factory.cookies[settings.SESSION_COOKIE_NAME] = session_id0
        request1 = self.get_request()
        visit1 = _get_visit(request1, 1)
        session_id1 = visit1.session_id
        self.assertTrue(session_id1)
        self.assertEqual(session_id1, request1.session.session_key)

        # Play with session to ensure this it's valid:
        request1.session['foo'] = 'bar'
        request1.session.save()
        self.assertEqual(session_id1, request1.session.session_key)
        self.assertEqual(request1.session['foo'], 'bar')

        self.assertNotEqual(visit1, visit0)
        self.assertNotEqual(session_id1, session_id0)
        self.assertEqual(models.relational.Visit.objects.count(), 2)


@patch.dict('django.conf.settings.WEB', mock_subdomain='testserver')
class TestEdgeFlipViews(EdgeFlipTestCase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestEdgeFlipViews, self).setUp()
        self.params = {
            'fbid': '1',
            'token': 1,
            'num': 9,
            'sessionid': 'fake-session',
            'campaignid': 1,
            'contentid': 1,
            'mockmode': True,
        }
        self.test_user = models.datastructs.UserInfo(
            uid=1,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            sex='male',
            birthday=timezone.datetime(1984, 1, 1, tzinfo=timezone.utc),
            city='Chicago',
            state='Illinois',
        )
        self.test_edge = models.datastructs.Edge(
            self.test_user,
            self.test_user,
            None
        )
        self.test_client = models.Client.objects.get(pk=1)
        self.test_cs = models.ChoiceSet.objects.create(
            client=self.test_client, name='Unit Tests')
        self.test_filter = models.ChoiceSetFilter.objects.create(
            filter_id=2, url_slug='all', choice_set=self.test_cs)

    def get_outgoing_url(self, redirect_url, campaign_id=None):
        if campaign_id:
            qs = '?' + urllib.urlencode({'campaignid': campaign_id})
        else:
            qs = ''
        url = reverse('outgoing', args=[self.test_client.fb_app_id,
                                         urllib.quote_plus(redirect_url)])
        return url + qs

    def test_faces_get(self):
        ''' Faces endpoint requires POST, so we expect a 405 here '''
        response = self.client.get(reverse('faces'))
        self.assertStatusCode(response, 405)

    @patch('targetshare.views.facebook.mock_client')
    def test_faces_initial_entry(self, fb_mock):
        ''' Tests a users first request to the Faces endpoint. We expect to
        receive a JSON response with a status of waiting along with the
        tasks IDs of the Celery jobs we started. We also expect to see an
        extended token saved to Dynamo
        '''
        fb_mock.extendTokenFb.return_value = models.dynamo.Token(
            token='test-token',
            fbid=1111111,
            appid=self.test_client.fb_app_id,
            expires=timezone.now()
        )
        expires0 = timezone.now() - datetime.timedelta(days=5)
        models.dynamo.Token.items.put_item(
            fbid=1111111,
            appid=self.test_client.fb_app_id,
            token='test-token',
            expires=expires0,
            overwrite=True,
        )
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        assert data['px3_task_id']
        assert data['px4_task_id']
        refreshed_token = models.dynamo.Token.items.get_item(
            fbid=1111111,
            appid=self.test_client.fb_app_id,
        )
        self.assertGreater(refreshed_token['expires'], expires0)

    def patch_ranking(self, celery_mock,
                      px3_ready=True, px3_successful=True,
                      px4_ready=True, px4_successful=True):
        if px3_ready:
            px3_failed = not px3_successful
        else:
            px3_successful = px3_failed = False

        if px4_ready:
            px4_failed = not px4_successful
        else:
            px4_successful = px4_failed = False

        error = ValueError('Ruh-Roh!')

        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = px3_ready
        px3_result_mock.successful.return_value = px3_successful
        px3_result_mock.failed.return_value = px3_failed
        if px3_ready:
            px3_result_mock.result = (
                [self.test_edge],
                models.datastructs.TieredEdges(edges=[self.test_edge], campaignId=1, contentId=1),
                self.test_filter.filter_id,
                self.test_filter.url_slug,
                1,
                1
            ) if px3_successful else error
        else:
            px3_result_mock.result = None

        px4_result_mock = Mock()
        px4_result_mock.ready.return_value = px4_ready
        px4_result_mock.successful.return_value = px4_successful
        px4_result_mock.failed.return_value = px4_failed
        if px4_ready:
            px4_result_mock.result = [self.test_edge] if px4_successful else error
        else:
            px4_result_mock.result = None

        async_mock = Mock()
        async_mock.side_effect = [
            px3_result_mock,
            px4_result_mock
        ]
        celery_mock.current_app.AsyncResult = async_mock

    @patch('targetshare.views.celery')
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

    @patch('targetshare.views.celery')
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

    @patch('targetshare.views.celery')
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
        self.assertStatusCode(response, 500)
        self.assertEqual(response.content, 'No friends identified for you.')

    @patch('targetshare.views.celery')
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

    @patch('targetshare.views.celery')
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
    @patch('targetshare.views.celery')
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

    def test_button_no_recs(self):
        ''' Tests views.button without style recs '''
        assert not models.Assignment.objects.exists()

        response = self.client.get(reverse('button', args=[1, 1]))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['fb_params'],
            {'fb_app_name': 'sharing-social-good',
             'fb_app_id': 471727162864364}
        )

        assignment = models.Assignment.objects.get()
        # This field is how we know the assignment came from a default:
        self.assertIsNone(assignment.feature_row)

    def test_button_with_recs(self):
        ''' Tests views.button with style recs '''
        # Create Button Styles
        campaign = models.Campaign.objects.get(pk=1)
        client = campaign.client
        for prob in xrange(1, 3):
            bs = client.buttonstyles.create(name='test')
            bs.buttonstylefiles.create(html_template='button.html')
            true_prob = prob / 2.0 # [0.5, 1]
            campaign.campaignbuttonstyles.create(
                button_style=bs, rand_cdf=Decimal(true_prob))

        assert not models.Assignment.objects.exists()
        response = self.client.get(reverse('button', args=[1, 1]))

        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['fb_params'],
            {'fb_app_name': 'sharing-social-good',
             'fb_app_id': 471727162864364}
        )
        assignment = models.Assignment.objects.get()
        chosen_from_rows = re.findall(r'\d+', assignment.chosen_from_rows)
        self.assertEqual(
            {int(choice) for choice in chosen_from_rows},
            set(campaign.campaignbuttonstyles.values_list('button_style', flat=True))
        )
        self.assertEqual(models.Event.objects.filter(event_type='session_start').count(), 1)

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

    def test_objects_hit_by_fb(self):
        ''' Test hitting the views.object endpoint as the FB crawler '''
        assert not models.Event.objects.exists()
        response = self.client.get(
            reverse('objects', args=[1, 1]),
            HTTP_USER_AGENT='facebookexternalhit'
        )
        self.assertStatusCode(response, 200)
        assert not models.Event.objects.filter(event_type='clickback').exists()
        assert response.context['fb_params']
        assert response.context['content']
        assert response.context['redirect_url']

    def test_objects(self):
        '''Test hitting the views.object endpoint with an activity id as a
        normal, non-fb bot, user

        '''
        self.assertFalse(models.Event.objects.exists())
        response = self.client.get(
            reverse('objects', args=[1, 1]),
            data={'fb_action_ids': 1, 'campaign_id': 1}
        )
        self.assertStatusCode(response, 200)
        self.assertTrue(models.Event.objects.filter(activity_id=1).exists())
        self.assertTrue(response.context['fb_params'])
        self.assertEqual(response.context['fb_params']['fb_object_url'],
                         'https://testserver/objects/1/1/?campaign_id=1&cssslug=')
        redirect_url = models.ClientContent.objects.get(pk=1).url
        self.assertEqual(response.context['redirect_url'],
                         self.get_outgoing_url(redirect_url, 1))
        self.assertTrue(response.context['content'])
        self.assertTrue(
            models.Event.objects.filter(
                event_type='clickback',
                campaign_id=1,
            ).exists()
        )

    def test_objects_source_url(self):
        fb_object = models.FBObject.objects.get(pk=1)
        campaign_fb_object = fb_object.campaignfbobjects.all()[0]
        campaign_fb_object.source_url = 'http://www.google.com/'
        campaign_fb_object.save()
        fb_object.campaignfbobjects.exclude(pk=campaign_fb_object.pk).delete()

        response = self.client.get(
            reverse('objects', args=[1, 1]),
            data={'fb_action_ids': 1, 'campaign_id': 1}
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['fb_params']['fb_object_url'],
                         'https://testserver/objects/1/1/?campaign_id=1&cssslug=')
        self.assertEqual(response.context['redirect_url'],
                         self.get_outgoing_url('http://www.google.com/', 1))

    def test_objects_ambiguous_source_url(self):
        fb_object = models.FBObject.objects.get(pk=1)
        fb_object.campaignfbobjects.create(
            campaign_id=1,
            source_url='http://www.google.com/',
        )
        response = self.client.get(
            reverse('objects', args=[1, 1]),
            data={'fb_action_ids': 1, 'campaign_id': 1}
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['fb_params']['fb_object_url'],
                         'https://testserver/objects/1/1/?campaign_id=1&cssslug=')
        self.assertGreater(fb_object.campaignfbobjects.count(), 1)
        self.assertEqual(response.context['redirect_url'],
                         self.get_outgoing_url('http://www.google.com/', 1))

    def test_suppress(self):
        ''' Test suppressing a user that was recommended '''
        assert not models.Event.objects.exists()
        response = self.client.post(
            reverse('suppress'), {
                'userid': 1,
                'appid': self.test_client.fb_app_id,
                'campaignid': 1,
                'contentid': 1,
                'content': 'Testing',
                'oldid': 2,
                'newid': 3,
                'fname': 'Suppress',
                'lname': 'Test',
            }
        )
        self.assertStatusCode(response, 200)
        assert models.Event.objects.filter(
            visit__fbid=1, friend_fbid=2, event_type='suppressed'
        ).exists()
        assert models.FaceExclusion.objects.filter(
            fbid=1, friend_fbid=2
        ).exists()
        assert models.Event.objects.filter(
            visit__fbid=1, friend_fbid=3, event_type='shown'
        ).exists()
        self.assertEqual(int(response.context['fbid']), 3)
        self.assertEqual(response.context['firstname'], 'Suppress')

    def test_record_event_forbidden(self):
        ''' Test views.record_event. Expects particular event_types to be
        sent, otherwise it returns a 403
        '''
        response = self.client.post(
            reverse('record-event'), {
                'userid': 1,
                'appid': self.test_client.fb_app_id,
                'campaignid': 1,
                'contentid': 1,
                'content': 'Testing',
                'actionid': 100,
                'friends[]': [10, 11, 12],
                'event_type': 'fake-event'
            }
        )
        self.assertStatusCode(response, 403)

    def test_record_event_shared(self):
        ''' Test views.record_event with shared event_type '''
        response = self.client.post(
            reverse('record-event'), {
                'userid': 1,
                'appid': self.test_client.fb_app_id,
                'campaignid': 1,
                'contentid': 1,
                'content': 'Testing',
                'actionid': 100,
                'friends[]': [10, 11, 12],
                'eventType': 'shared',
                'shareMsg': 'Testing Share'
            }
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(
            models.Event.objects.filter(
                event_type='shared', friend_fbid__in=[10, 11, 12]
            ).count(), 3
        )
        self.assertEqual(
            models.FaceExclusion.objects.filter(
                friend_fbid__in=[10, 11, 12]
            ).count(), 3
        )
        assert models.ShareMessage.objects.filter(
            activity_id=100, fbid=1, campaign_id=1,
            content_id=1, message='Testing Share'
        ).exists()

    def test_record_event_button_click(self):
        ''' Test views.record_event with shared event_type '''
        response = self.client.post(
            reverse('record-event'), {
                'userid': 1,
                'appid': self.test_client.fb_app_id,
                'campaignid': 1,
                'contentid': 1,
                'content': 'Testing',
                'actionid': 100,
                'eventType': 'button_click',
                'shareMsg': 'Testing Share'
            }
        )
        self.assertStatusCode(response, 200)
        assert models.Event.objects.get(event_type='button_click')

    def test_record_event_button_load_dupe(self):
        ''' Test that views.record_event will not create duplicate
        button_load events
        '''
        response = self.client.post(
            reverse('record-event'), {
                'userid': 1,
                'appid': self.test_client.fb_app_id,
                'campaignid': 1,
                'contentid': 1,
                'content': 'Testing',
                'actionid': 100,
                'eventType': 'button_load',
                'shareMsg': 'Testing Share'
            }
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(
            models.Event.objects.filter(event_type='button_load').count(),
            1
        )
        # Now round 2, shouldn't produce a new event
        response = self.client.post(
            reverse('record-event'), {
                'userid': 1,
                'appid': self.test_client.fb_app_id,
                'campaignid': 1,
                'contentid': 1,
                'content': 'Testing',
                'actionid': 100,
                'eventType': 'button_load',
                'shareMsg': 'Testing Share'
            }
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(
            models.Event.objects.filter(event_type='button_load').count(),
            1
        )

    @patch('targetshare.views.facebook.client')
    def test_record_event_authorized(self, fb_mock):
        ''' Test views.record_event with authorized event_type '''
        fb_mock.extendTokenFb.return_value = models.dynamo.Token(
            token='test-token',
            fbid=1111111,
            appid=self.test_client.fb_app_id,
            expires=timezone.now()
        )
        expires0 = timezone.now() - datetime.timedelta(days=5)
        models.dynamo.Token.items.put_item(
            fbid=1111111,
            appid=self.test_client.fb_app_id,
            token='test-token',
            expires=expires0,
            overwrite=True,
        )
        response = self.client.post(
            '%s?token=1' % reverse('record-event'), {
                'userid': 1111111,
                'appid': self.test_client.fb_app_id,
                'campaignid': 1,
                'contentid': 1,
                'content': 'Testing',
                'actionid': 100,
                'friends[]': [10, 11, 12], # jQuery thinks it's clever with []
                'eventType': 'authorized',
                'shareMsg': 'Testing Share',
                'token': 'test-token',
                'extend_token': 'True'
            }
        )
        self.assertStatusCode(response, 200)
        refreshed_token = models.dynamo.Token.items.get_item(
            fbid=1111111,
            appid=self.test_client.fb_app_id,
        )
        self.assertGreater(refreshed_token['expires'], expires0)
        events = models.Event.objects.filter(
            event_type='authorized',
            friend_fbid__in=[10, 11, 12]
        )
        self.assertEqual(events.count(), 3)

    def test_canvas(self):
        ''' Tests views.canvas '''
        response = self.client.get(reverse('canvas'))
        self.assertStatusCode(response, 200)

    def test_canvas_encoded(self):
        ''' Testing the views.frame_faces_encoded method '''
        response = self.client.get(
            reverse('canvas-faces-encoded', args=['uJ3QkxA4XIk%3D'])
        )
        self.assertStatusCode(response, 200)

    def test_canvas_encoded_noslash(self):
        """Encoded canvas endpoint responds with 200 without trailing slash."""
        url = reverse('canvas-faces-encoded', args=['uJ3QkxA4XIk%3D'])
        response = self.client.get(url.rstrip('/'))
        self.assertStatusCode(response, 200)

    @patch('targetshare.views.facebook.client')
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
            print event_type
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
            response.context['user'].id,
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
