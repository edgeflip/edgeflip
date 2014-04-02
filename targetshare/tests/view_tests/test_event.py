import datetime

from django.core.urlresolvers import reverse
from django.utils import timezone
from mock import patch

from targetshare import models

from .. import EdgeFlipViewTestCase


@patch.dict('django.conf.settings.WEB', mock_subdomain='testserver')
class TestEventViews(EdgeFlipViewTestCase):

    fixtures = ['test_data']

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
            visit__visitor__fbid=1, friend_fbid=2, event_type='suppressed'
        ).exists()
        assert models.FaceExclusion.objects.filter(
            fbid=1, friend_fbid=2
        ).exists()
        assert models.Event.objects.filter(
            visit__visitor__fbid=1, friend_fbid=3, event_type='shown'
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

    @patch('targetshare.views.events.facebook.client')
    def test_record_event_authorized(self, fb_mock):
        ''' Test views.record_event with authorized event_type '''
        fb_mock.extend_token.return_value = models.dynamo.Token(
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
        events = models.Event.objects.filter(event_type='authorized')
        self.assertEqual(events.count(), 0)

        response = self.client.post(reverse('record-event'), {
            'token': 'test-token',
            'userid': 1111111,
            'appid': self.test_client.fb_app_id,
            'campaignid': 1,
            'contentid': 1,
            'content': 'Testing',
            'eventType': 'authorized',
            'token': 'test-token',
            'extend_token': '1'
        })
        self.assertStatusCode(response, 200)
        refreshed_token = models.dynamo.Token.items.get_item(
            fbid=1111111,
            appid=self.test_client.fb_app_id,
        )
        self.assertGreater(refreshed_token['expires'], expires0)
        self.assertEqual(events.count(), 1)

    @patch('targetshare.views.events.facebook.client')
    def test_record_event_preauthed(self, fb_mock):
        # Make bad request to init visit
        response = self.client.post(reverse('record-event'), {
            'eventType': 'no-events-here',
            'appid': self.test_client.fb_app_id,
        })
        self.assertStatusCode(response, 403)

        visit = models.Visit.objects.get(session_id=self.client.cookies['sessionid'].value)
        visit.events.create(event_type='authorized')

        auths = models.Event.objects.filter(event_type='authorized')
        self.assertEqual(auths.count(), 1)

        response = self.client.post(reverse('record-event'), {
            'userid': 1111111,
            'appid': self.test_client.fb_app_id,
            'campaignid': 1,
            'contentid': 1,
            'content': 'Testing',
            'eventType': 'authorized',
            'token': 'test-token',
            'extend_token': 'True'
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(auths.count(), 1)
        self.assertEqual(fb_mock.extend_token.call_count, 1)

    def test_record_event_heartbeat(self):
        ''' Testing the record_event view with a heartbeat event '''
        response = self.client.post(
            reverse('record-event'), {
                'userid': 1,
                'appid': self.test_client.fb_app_id,
                'campaignid': 1,
                'contentid': 1,
                'content': 'Testing',
                'actionid': 100,
                'eventType': 'heartbeat',
            }
        )
        self.assertStatusCode(response, 200)

        event = models.Event.objects.get(event_type='heartbeat')
        self.assertEqual(event.content, '1')
        self.assertEqual(event.campaign_id, 1)
        self.assertEqual(event.client_content_id, 1)

        response = self.client.post(
            reverse('record-event'), {
                'userid': 1,
                'appid': self.test_client.fb_app_id,
                'campaignid': 1,
                'contentid': 1,
                'content': 'Testing',
                'actionid': 100,
                'eventType': 'heartbeat',
            }
        )
        self.assertStatusCode(response, 200)

        event = models.Event.objects.get(event_type='heartbeat')
        self.assertEqual(event.content, '2')
        self.assertEqual(event.campaign_id, 1)
        self.assertEqual(event.client_content_id, 1)

    def test_update_event_heartbeat_meta(self):
        """heartbeat metadata updated but not overwritten"""
        response = self.client.post(
            reverse('record-event'), {
                'userid': 1,
                'appid': self.test_client.fb_app_id,
                'content': 'Testing',
                'actionid': 100,
                'eventType': 'heartbeat',
            }
        )
        self.assertStatusCode(response, 200)

        event = models.Event.objects.get(event_type='heartbeat')
        self.assertEqual(event.content, '1')
        self.assertIsNone(event.campaign_id, 1)
        self.assertIsNone(event.client_content_id, 1)

        response = self.client.post(
            reverse('record-event'), {
                'userid': 1,
                'appid': self.test_client.fb_app_id,
                'campaignid': 1,
                'contentid': 1,
                'content': 'Testing',
                'actionid': 100,
                'eventType': 'heartbeat',
            }
        )
        self.assertStatusCode(response, 200)

        event = models.Event.objects.get(event_type='heartbeat')
        self.assertEqual(event.content, '2')
        self.assertEqual(event.campaign_id, 1)
        self.assertEqual(event.client_content_id, 1)

        response = self.client.post(
            reverse('record-event'), {
                'userid': 1,
                'appid': self.test_client.fb_app_id,
                'campaignid': 2,
                'contentid': 2,
                'content': 'Testing',
                'actionid': 100,
                'eventType': 'heartbeat',
            }
        )
        self.assertStatusCode(response, 200)

        event = models.Event.objects.get(event_type='heartbeat')
        self.assertEqual(event.content, '3')
        self.assertEqual(event.campaign_id, 1)
        self.assertEqual(event.client_content_id, 1)
