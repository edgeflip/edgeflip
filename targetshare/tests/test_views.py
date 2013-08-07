import json
from decimal import Decimal
from datetime import date, timedelta

from django.core.urlresolvers import reverse
from django.utils import timezone
from mock import patch, Mock

from targetshare import datastructs, models, client_db_tools as cdb

from . import EdgeFlipTestCase


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
        self.test_user = datastructs.UserInfo(
            uid=1,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            sex='male',
            birthday=date(1984, 1, 1),
            city='Chicago',
            state='Illinois',
        )
        self.test_edge = datastructs.Edge(
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

    def test_faces_initial_entry(self):
        ''' Tests a users first request to the Faces endpoint. We expect to
        receive a JSON response with a status of waiting along with the
        tasks IDs of the Celery jobs we started
        '''
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        assert data['px3_task_id']
        assert data['px4_task_id']

    def test_faces_invalid_subdomain(self):
        ''' Test hitting the faces endpoint from an invalid domain '''
        self.test_client.subdomain = 'invalidsubdomain'
        self.test_client.save()
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 404)

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
    def test_faces_last_call(self, celery_mock):
        ''' Test that gives up on waiting for the px4 result, and serves the
        px3 results
        '''
        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = True
        px3_result_mock.result = (
            [self.test_edge],
            cdb.TieredEdges(edges=[self.test_edge], campaignId=1, contentId=1),
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
            cdb.TieredEdges(edges=[self.test_edge], campaignId=1, contentId=1),
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

    def test_button_no_recs(self):
        ''' Tests views.button without style recs '''
        response = self.client.get(reverse('button', args=[1, 1]))
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response.context['fb_params'],
            {'fb_app_name': 'sharing-social-good', 'fb_app_id': '471727162864364'}
        )
        assert not models.Assignment.objects.exists()

    def test_button_with_recs(self):
        ''' Tests views.button with style recs '''
        # Create Button Styles
        campaign = models.Campaign.objects.get(pk=1)
        client = campaign.client
        bs = models.ButtonStyle.objects.create(
            client=client, name='test')
        models.ButtonStyleFile.objects.create(
            html_template='targetshare/button.html', button_style=bs)
        models.CampaignButtonStyle.objects.create(
            campaign=campaign, button_style=bs,
            rand_cdf=Decimal('1.000000')
        )
        assert not models.Assignment.objects.exists()
        response = self.client.get(reverse('button', args=[1, 1]))
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response.context['fb_params'],
            {'fb_app_name': 'sharing-social-good', 'fb_app_id': '471727162864364'}
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
        client = models.Client.objects.get(campaign__pk=1)
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

    def test_frame_faces_test_mode_bad_request(self):
        ''' Tests views.frame_faces with test_mode enabled, but without
        providing a test FB ID or Token
        '''
        response = self.client.get(reverse('frame-faces', args=[1, 1]), {
            'test_mode': True
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
        assert not models.Event.objects.exists()
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
            fbid=1, friend_fbid=2, event_type='suppress'
        ).exists()
        assert models.FaceExclusion.objects.filter(
            fbid=1, friend_fbid=2
        ).exists()
        assert models.Event.objects.filter(
            fbid=1, friend_fbid=3, event_type='shown'
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
                'friends': [10, 11, 12],
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
                'friends': [10, 11, 12],
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

    @patch('targetshare.views.facebook')
    def test_record_event_authorized(self, fb_mock):
        ''' Test views.record_event with authorized event_type '''
        fb_mock.extendToken.return_value = None
        token = models.Token.objects.create(
            fbid=1111111, app_id=self.test_client.fb_app_id,
            token='test-token', owner_id=1111111,
            expires=timezone.now() - timedelta(days=5)
        )
        response = self.client.post(
            '%s?token=1' % reverse('record-event'), {
                'userid': 1111111,
                'appid': self.test_client.fb_app_id,
                'campaignid': 1,
                'contentid': 1,
                'content': 'Testing',
                'actionid': 100,
                'friends': [10, 11, 12],
                'eventType': 'authorized',
                'shareMsg': 'Testing Share',
                'token': 'test-token'
            }
        )
        self.assertStatusCode(response, 200)
        refreshed_token = models.Token.objects.get(pk=token.pk)
        assert refreshed_token.expires > token.expires
        self.assertEqual(
            models.Event.objects.filter(
                event_type='authorized', friend_fbid__in=[10, 11, 12]
            ).count(), 3
        )

    def test_canvas(self):
        ''' Tests views.canvas '''
        response = self.client.get(reverse('canvas'))
        self.assertStatusCode(response, 200)

    @patch('targetshare.views.facebook')
    def test_health_check(self, fb_mock):
        ''' Tests views.health_check '''
        fb_mock.getUrlFb.return_value = {'id': 6963}
        response = self.client.get(reverse('health-check'))
        self.assertStatusCode(response, 200)
        self.assertEqual(
            json.loads(response.content), {
                'database': True,
                'facebook': True
            }
        )

    def test_health_check_elb(self):
        ''' Test health-check view from Amazon ELB perspective '''
        response = self.client.get(reverse('health-check'), {'elb': True})
        self.assertStatusCode(response, 200)
        self.assertEqual(response.content, "It's Alive!")
