import datetime
import json
import re
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

    def test_faces_get(self):
        ''' Faces endpoint requires POST, so we expect a 405 here '''
        response = self.client.get(reverse('faces'))
        self.assertStatusCode(response, 405)

    @patch('targetshare.views.mock_facebook')
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

    @patch('targetshare.views.celery')
    def test_faces_px3_wait(self, celery_mock):
        ''' Tests that we receive a JSON status of "waiting" when our px3
        task isn't yet complete
        '''
        result_mock = Mock()
        result_mock.ready.return_value = False
        result_mock.successful.return_value = False
        result_mock.failed.return_value = False
        async_mock = Mock()
        async_mock.side_effect = [
            result_mock,
            result_mock
        ]
        celery_mock.current_app.AsyncResult = async_mock
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
        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = True
        px3_result_mock.successful.return_value = True
        px3_result_mock.failed.return_value = False
        px4_result_mock = Mock()
        px4_result_mock.ready.return_value = False
        async_mock = Mock()
        async_mock.side_effect = [
            px3_result_mock,
            px4_result_mock
        ]
        celery_mock.current_app.AsyncResult = async_mock
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
        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = True
        px3_result_mock.successful.return_value = False
        px3_result_mock.failed.return_value = True
        px3_result_mock.result = ValueError('Ruh-Roh!')
        px4_result_mock = Mock()
        px4_result_mock.ready.return_value = False
        async_mock = Mock()
        async_mock.side_effect = [
            px3_result_mock,
            px4_result_mock
        ]
        celery_mock.current_app.AsyncResult = async_mock
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
        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = True
        px3_result_mock.result = (
            [self.test_edge],
            models.datastructs.TieredEdges(edges=[self.test_edge], campaignId=1, contentId=1),
            self.test_filter.filter_id,
            self.test_filter.url_slug,
            1,
            1
        )
        px4_result_mock = Mock()
        px4_result_mock.ready.return_value = False
        px4_result_mock.successful.return_value = False
        async_mock = Mock()
        async_mock.side_effect = [
            px3_result_mock,
            px4_result_mock
        ]
        celery_mock.current_app.AsyncResult = async_mock
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
        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = True
        px3_result_mock.result = (
            [self.test_edge],
            models.datastructs.TieredEdges(edges=[self.test_edge], campaignId=1, contentId=1),
            self.test_filter.filter_id,
            self.test_filter.url_slug,
            1,
            1
        )
        px4_result_mock = Mock()
        px4_result_mock.ready.return_value = True
        px4_result_mock.successful.return_value = True
        px4_result_mock.result = [self.test_edge]
        async_mock = Mock()
        async_mock.side_effect = [
            px3_result_mock,
            px4_result_mock
        ]
        celery_mock.current_app.AsyncResult = async_mock
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
        self.assertEqual({int(choice) for choice in chosen_from_rows},
                         set(campaign.campaignbuttonstyles.values_list('pk', flat=True)))
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
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response.context['campaign'],
            models.Campaign.objects.get(pk=1)
        )
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
        assert models.Event.objects.get(event_type='session_start')
        assert models.Event.objects.get(event_type='faces_page_load')

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
        ''' Test hitting the views.object endpoint with an activity id as a
        normal, non-fb bot, user
        '''
        assert not models.Event.objects.exists()
        response = self.client.get(
            reverse('objects', args=[1, 1]),
            data={'fb_action_ids': 1}
        )
        self.assertStatusCode(response, 200)
        assert models.Event.objects.filter(activity_id=1).exists()
        assert response.context['fb_params']
        assert response.context['content']
        assert response.context['redirect_url']
        assert models.Event.objects.filter(event_type='clickback').exists()

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

    @patch('targetshare.views.facebook')
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

    @patch('targetshare.views.facebook')
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
            campaign_id=1, content_id=1, fbid=100, uuid='100',
            app_id=self.test_client.fb_app_id,
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
                event_type=event_type, notification=notification
            )

        response = self.client.get(
            reverse('faces-email', args=[notification.uuid])
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
