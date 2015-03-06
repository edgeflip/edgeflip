import datetime
import json
import os.path
import re

from django.conf import settings
from django.contrib.auth import models as auth
from django.core.urlresolvers import reverse
from django.utils import timezone
from mock import patch, Mock

from targetshare import models

from .. import EdgeFlipViewTestCase, DATA_PATH, patch_facebook


@patch('targetshare.views.faces.celery')
class TestFaces(EdgeFlipViewTestCase):

    fixtures = ['test_data']

    task_key = 'faces_tasks_px_1_1_1_1.0'
    task_ids = [[3, '123'], [4, '1234']]

    def setUp(self):
        super(TestFaces, self).setUp()
        self.url = reverse('targetshare:faces')

        self.session = self.get_session()
        self.session.set_test_cookie() # usually set by frame_faces
        self.set_session(self.session)

    def make_post(self, data=()):
        response = self.client.post(self.url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response.data = json.loads(response.content) if 200 <= response.status_code < 300 else None
        return response

    def test_get(self, _celery_mock):
        """Response to GET is code 405"""
        response = self.client.get(self.url)
        self.assertStatusCode(response, 405)

    @patch_facebook
    def test_fallback_campaign_rejection(self, _celery_mock):
        """(Initially-requested) campaign must be root"""
        root_campaigns = models.CampaignProperties.objects.values_list('root_campaign', flat=True)
        root_campaign_id = root_campaigns.get(campaign_id=6)
        self.assertEqual(root_campaign_id, 5) # 6 is fallback of 5
        response = self.make_post(dict(self.params, campaign=6))
        self.assertStatusCode(response, 400)

    @patch_facebook
    def test_initial_entry(self, _celery_mock):
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

        response = self.make_post(self.params)
        self.assertStatusCode(response, 200) # eager celery completes targeting

        self.assertEqual(response.data['campaignid'], 1)
        self.assertEqual(response.data['contentid'], 1)

        task_ids = self.client.session['faces_tasks_px_1111111_1_1_1.0']
        self.assertEqual(len(task_ids), 2)

        refreshed_token = models.dynamo.Token.items.lookup(fbid, self.test_client.fb_app_id)
        self.assertGreater(refreshed_token.expires, expires0)
        self.assertEqual(clientuser.count(), 1)

    def test_px3_wait(self, celery_mock):
        """Receive "waiting" response when px3 task incomplete"""
        self.patch_targeting(celery_mock, px3_ready=False, px4_ready=False)
        self.session[self.task_key] = self.task_ids
        self.session.save()

        response = self.make_post(self.params)
        self.assertStatusCode(response, 202)
        self.assertEqual(response.data['status'], 'waiting')
        self.assertEqual(response.data['reason'], "Identifying friends.")

        session = self.client.session
        self.assertEqual(set(session.keys()), {'sessionverified', self.task_key})
        self.assertEqual(session[self.task_key], self.task_ids)

    def test_px4_wait(self, celery_mock):
        """Receive "waiting" response when px3 task complete but px4 incomplete"""
        self.patch_targeting(celery_mock, px4_ready=False)
        self.session[self.task_key] = self.task_ids
        self.session.save()

        response = self.make_post(self.params)
        self.assertStatusCode(response, 202)
        self.assertEqual(response.data['status'], 'waiting')
        self.assertEqual(response.data['reason'], "Identifying friends.")

        session = self.client.session
        self.assertEqual(set(session.keys()), {'sessionverified', self.task_key})
        self.assertEqual(session[self.task_key], self.task_ids)

    def test_px3_fail(self, celery_mock):
        """Receive error response as soon as px3 task fails"""
        self.patch_targeting(celery_mock, px3_successful=False, px4_ready=False)
        self.session[self.task_key] = self.task_ids
        self.session.save()
        response = self.make_post(self.params)
        self.assertContains(response, 'No friends were identified for you.', status_code=500)

    def test_px3_fail_px4_success(self, celery_mock):
        """Receive error response px3 task fails despite px4 success"""
        self.patch_targeting(celery_mock, px3_successful=False, px4_ready=True)
        self.session[self.task_key] = self.task_ids
        self.session.save()
        response = self.make_post(self.params)
        self.assertContains(response, 'No friends were identified for you.', status_code=500)

    def test_last_call(self, celery_mock):
        """Receive px3 results on last call if px4 not ready"""
        self.patch_targeting(celery_mock, px4_ready=False)
        self.session[self.task_key] = self.task_ids
        self.session.save()
        response = self.make_post(dict(self.params, last_call=True))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['html'])

    @patch('targetshare.views.faces.LOG')
    def test_px3_fail_last_call(self, logger_mock, celery_mock):
        """Receive 503 response to last call request if there are no results"""
        self.patch_targeting(celery_mock, px3_ready=False, px4_ready=False)
        self.session[self.task_key] = self.task_ids
        self.session.save()
        response = self.make_post(dict(self.params, last_call=True))
        self.assertContains(response, 'Response has taken too long, giving up', status_code=503)
        self.assertIn('primary targeting task (px%s) failed to complete',
                      logger_mock.fatal.call_args[0][0])

    def test_px4_filtering(self, celery_mock):
        self.test_edges = [self.test_edge._replace(px3_score=1.0, px4_score=1.5)]
        self.patch_targeting(celery_mock, px4_filtering=True)
        self.session[self.task_key] = self.task_ids
        self.session.save()
        response = self.make_post(self.params)
        self.assertStatusCode(response, 200)

        visit = models.Visit.objects.get(session_id=self.session.session_key)
        generated = visit.events.get(event_type='generated')
        shown = visit.events.get(event_type='shown')
        self.assertEqual(generated.content, 'px3_score: 1.0 (123), px4_score: 1.5 (1234) : Test User')
        self.assertEqual(shown.content, 'px4_score: 1.5 (1234) : Test User')

    def test_complete_crawl(self, celery_mock):
        ''' Test that completes both px3 and px4 crawls '''
        self.test_edges = [self.test_edge._replace(px3_score=1.0, px4_score=1.5)]
        self.patch_targeting(celery_mock)
        self.session[self.task_key] = self.task_ids
        self.session.save()
        response = self.make_post(self.params)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['html'])

        visit = models.Visit.objects.get(session_id=self.session.session_key)
        generated = visit.events.get(event_type='generated')
        shown = visit.events.get(event_type='shown')
        self.assertEqual(generated.content, 'px3_score: 1.0 (123), px4_score: 1.5 (1234) : Test User')
        self.assertEqual(shown.content, 'px4_score: 1.5 (1234) : Test User')

    def test_reload(self, celery_mock):
        self.test_edges = [self.test_edge._replace(px3_score=1.0, px4_score=1.5)]

        self.patch_targeting(celery_mock)
        self.session[self.task_key] = self.task_ids
        self.session.save()
        response = self.make_post(self.params)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['html'])

        visit = models.Visit.objects.get(session_id=self.session.session_key)
        events = visit.events.all()
        generated0 = events.filter(event_type='generated').count()
        shown0 = events.filter(event_type='shown').count()
        self.assertEqual(shown0, 1)
        self.assertEqual(generated0, 1)

        self.patch_targeting(celery_mock)
        response = self.make_post(self.params)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['html'])

        generated1 = events.filter(event_type='generated').count()
        shown1 = events.filter(event_type='shown').count()
        self.assertEqual(shown1, shown0 * 2)
        self.assertEqual(generated1, generated0)

    @patch_facebook
    def test_cookieless_client_spam(self, celery_mock):
        targeting = models.Event.objects.filter(event_type='targeting_requested')

        del self.client.cookies[settings.SESSION_COOKIE_NAME] # client is diabetic
        response = self.make_post(self.params)
        self.assertStatusCode(response, 202)
        self.assertEqual(response.data['status'], 'waiting')
        self.assertEqual(response.data['reason'], "Cookies are required. Please try again.")

        # We didn't do anything:
        self.assertFalse(targeting.exists())
        self.assertFalse(celery_mock.current_app.AsyncResult.called)
        # ... except start a new test:
        self.assertEqual(self.client.session.keys(), ['testcookie'])

        # But if they can hold the session this time...
        response = self.make_post(self.params)
        self.assertStatusCode(response, 200)
        self.assertEqual(targeting.get().visit.session_id, self.client.session.session_key)
        self.assertEqual(response.data['status'], 'success') # eager celery completes targeting

    def test_cookieless_client_failure(self, celery_mock):
        targeting = models.Event.objects.filter(event_type='targeting_requested')

        del self.client.cookies[settings.SESSION_COOKIE_NAME] # client is diabetic
        response = self.make_post(dict(self.params, last_call=True))
        self.assertContains(response, "Cookies are required.", status_code=403)

        # We didn't do anything:
        self.assertEqual(self.client.session.keys(), [])
        self.assertFalse(targeting.exists())
        self.assertFalse(celery_mock.current_app.AsyncResult.called)

    def test_session_exclusion(self, celery_mock):
        user2 = models.User(self.test_user, fbid=2)
        self.test_edges = [
            self.test_edge._replace(px3_score=1.0, px4_score=1.5),
            self.test_edge._replace(secondary=user2, px3_score=1.0, px4_score=1.5),
        ]

        self.patch_targeting(celery_mock)
        self.session[self.task_key] = self.task_ids
        self.session['face_exclusions_1_1_1'] = [1]
        self.session.save()
        response = self.make_post(self.params)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['html'])

        visit = models.Visit.objects.get(session_id=self.session.session_key)
        events = visit.events.all()
        generated0 = events.filter(event_type='generated').count()
        shown0 = events.filter(event_type='shown').count()
        self.assertEqual(shown0, 1)
        self.assertEqual(generated0, 2)

    def test_full_session_exclusion(self, celery_mock):
        self.test_edges = [self.test_edge._replace(px3_score=1.0, px4_score=1.5)]
        self.patch_targeting(celery_mock)
        self.session[self.task_key] = self.task_ids
        self.session['face_exclusions_1_1_1'] = [1]
        self.session.save()
        response = self.make_post(self.params)
        self.assertContains(response, "No friends remaining.", status_code=500)

    @patch('targetshare.integration.facebook.third_party.requests.get')
    def test_client_fbobject(self, get_mock, celery_mock):
        with open(os.path.join(DATA_PATH, 'gg.html')) as rh:
            get_mock.return_value = Mock(text=rh.read())

        source_url = 'http://somedomain/somepath/'
        self.params['efobjsrc'] = source_url
        campaign_objs = models.CampaignFBObject.objects.filter(source_url=source_url)
        self.assertFalse(campaign_objs.exists())

        self.patch_targeting(celery_mock)
        self.session[self.task_key] = self.task_ids
        self.session.save()
        response = self.make_post(self.params)
        self.assertStatusCode(response, 200)
        self.assertEqual(response.data['status'], 'success')

        # Assert second request doesn't hit client site:
        self.assertEqual(get_mock.call_count, 1)
        self.patch_targeting(celery_mock)
        response1 = self.make_post(self.params)
        self.assertStatusCode(response1, 200)
        self.assertEqual(response1.data['status'], 'success')
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
        self.assertIn(obj_attrs.og_image, response.data['html'])
        self.assertIn(obj_attrs.og_image, response1.data['html'])


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
        response = self.client.get(reverse('targetshare:frame-faces-default', args=[1, 1]))

        url = '//assets-edgeflip.s3.amazonaws.com/s/c/edgeflip-base-0.css'
        self.assertEqual(page_style.url, url)
        link_html = '<link rel="stylesheet" type="text/css" href="{}" />'.format(url)
        self.assertContains(response, link_html, count=1, html=True)

        assignment = models.Assignment.objects.get(feature_type='page_style_set_id')
        self.assertEqual(assignment.feature_row, campaign_page_style_set.page_style_set_id)

    def test_encoded(self):
        ''' Testing the views.frame_faces_encoded method '''
        response = self.client.get(
            reverse('targetshare:frame-faces-encoded', args=['t0AGY7FMXjM%3D'])
        )
        self.assertStatusCode(response, 200)

    def test_frame_faces(self):
        ''' Testing views.frame_faces '''
        self.assertFalse(models.Event.objects.exists())
        response = self.client.get(reverse('targetshare:frame-faces-default', args=[1, 1]))
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
                'fb_app_name': client.fb_app.name,
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

    def test_fallback_campaign_rejection(self):
        """Campaign must be root"""
        root_campaigns = models.CampaignProperties.objects.values_list('root_campaign', flat=True)
        root_campaign_id = root_campaigns.get(campaign_id=6)
        self.assertEqual(root_campaign_id, 5) # 6 is fallback of 5
        response = self.client.get(reverse('targetshare:frame-faces-default', args=[6, 1]))
        self.assertStatusCode(response, 404)

    def test_configurable_urls(self):
        success_url = '//disney.com/'
        error_url = 'http://www.google.com/foo/bar'
        response = self.client.get(reverse('targetshare:frame-faces-default', args=[1, 1]), {
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
        response = self.client.get(reverse('targetshare:frame-faces-default', args=[1, 1]), {
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
        response = self.client.get(reverse('targetshare:frame-faces-default', args=[1, 1]), {
            'secret': settings.TEST_MODE_SECRET[:4] + 'oops',
            'fbid': 1234,
            'token': 'oops',
        })
        self.assertStatusCode(response, 200)
        test_mode = response.context['test_mode']
        self.assertFalse(test_mode)
        self.assertIsNone(test_mode.fbid)
        self.assertIsNone(test_mode.token)

    def test_draft_mode(self):
        campaign = models.Campaign.objects.get(campaign_id=1)
        campaign.campaignproperties.update(
            status=models.CampaignProperties.Status.DRAFT,
        )

        user = auth.User.objects.create_user('mockuser', password='1234')
        group = user.groups.create(name='mockgroup')
        campaign.client.auth_groups.add(group)

        logged_in = self.client.login(username='mockuser', password='1234')
        self.assertTrue(logged_in)

        response = self.client.get(reverse('targetshare:frame-faces-default', args=[1, 1]))
        self.assertStatusCode(response, 200)
        self.assertTrue(response.context['draft_preview'])

    def test_draft_mode_denied(self):
        models.CampaignProperties.objects.filter(campaign_id=1).update(
            status=models.CampaignProperties.Status.DRAFT,
        )
        response = self.client.get(reverse('targetshare:frame-faces-default', args=[1, 1]))
        self.assertStatusCode(response, 403)

    def test_inactive_campaign(self):
        campaign = models.Campaign.objects.get(campaign_id=1)
        campaign.campaignproperties.update(
            status=models.CampaignProperties.Status.INACTIVE,
        )
        response = self.client.get(reverse('targetshare:frame-faces-default', args=[1, 1]))
        self.assertContains(response, "Page removed", status_code=410)

    def test_inactive_campaign_redirect(self):
        campaign = models.Campaign.objects.get(campaign_id=1)
        campaign.campaignproperties.update(
            status=models.CampaignProperties.Status.INACTIVE,
        )
        client = campaign.client
        client.campaign_inactive_url = 'http://clienthost/'
        client.save()
        outgoing_url = "{}?campaignid={}".format(
            reverse('targetshare:outgoing', args=[client.fb_app_id, client.campaign_inactive_url]),
            campaign.campaign_id,
        )

        # JavaScript redirect to overcome canvas iframe:
        response = self.client.get(reverse('targetshare:frame-faces-default', args=[1, 1]))
        self.assertStatusCode(response, 200)
        self.assertTemplateUsed(response, 'core/campaignstatus/inactive-campaign.html')
        self.assertFalse(response.context['authorized'])
        self.assertEqual(response.context['redirect_url'], outgoing_url)
        snippet = r'''outgoingRedirect\(['"]{}['"]\);\s*</script>'''.format(re.escape(outgoing_url))
        self.assertRegexpMatches(response.content, snippet)

    def test_canvas(self):
        ''' Tests views.canvas '''
        response = self.client.get(reverse('targetshare-canvas-root:canvas'))
        self.assertStatusCode(response, 200)

    def test_canvas_encoded(self):
        ''' Testing the views.frame_faces_encoded method '''
        self.assertFalse(models.Event.objects.exists())
        response = self.client.get(
            reverse('targetshare-canvas:frame-faces-encoded', args=['t0AGY7FMXjM%3D'])
        )
        self.assertStatusCode(response, 200)
        assert models.Event.objects.get(event_type='session_start')
        assert models.Event.objects.get(event_type='faces_page_load')
        assert models.Event.objects.get(event_type='faces_canvas_load')

    def test_canvas_encoded_noslash(self):
        """Encoded canvas endpoint responds with 200 without trailing slash."""
        url = reverse('targetshare-canvas:frame-faces-encoded', args=['t0AGY7FMXjM%3D'])
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
        for x in range(1, 8):
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
            if x > 3:
                event_type = 'generated'
            models.NotificationEvent.objects.create(
                campaign_id=1, client_content_id=1, friend_fbid=x,
                event_type=event_type, notification_user=notification_user
            )

        response = self.client.get(reverse('targetshare:faces-email', args=[notification_user.uuid]))
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['show_faces']), 3)
        self.assertEqual(len(response.context['all_friends']), 7)
        self.assertEqual(response.context['user'].fbid, 100)
        self.assertEqual(models.Event.objects.filter(event_type='faces_email_page_load').count(), 1)
        self.assertEqual(models.Event.objects.filter(event_type='shown').count(), 3)
        self.assertEqual(models.Event.objects.filter(event_type='generated').count(), 4)


@patch('targetshare.views.faces.celery')
class TestFrameFacesEagerTargeting(EdgeFlipViewTestCase):

    fixtures = ['test_data']

    oauth_task_id = 'OAUTH_TOKEN_TASK-1'

    faces_task_key = 'faces_tasks_px_1_1_1_1.0'

    def setUp(self):
        super(TestFrameFacesEagerTargeting, self).setUp()
        self.url = reverse('targetshare:frame-faces-default', args=[1, 1])

        self.session = self.get_session()
        self.session['oauth_task'] = self.oauth_task_id
        self.set_session(self.session)

    def test_pending(self, celery_mock):
        task = celery_mock.current_app.AsyncResult.return_value
        task.ready.return_value = False
        response = self.client.get(self.url)
        self.assertStatusCode(response, 200)
        self.assertEqual(len(task.method_calls), 1)
        session = self.client.session
        self.assertEqual(session['oauth_task'], self.oauth_task_id)
        self.assertNotIn(self.faces_task_key, session)

    def test_failed(self, celery_mock):
        task = celery_mock.current_app.AsyncResult.return_value
        task.ready.return_value = True
        task.successful.return_value = False
        response = self.client.get(self.url)
        self.assertStatusCode(response, 200)
        self.assertEqual(len(task.method_calls), 2)
        session = self.client.session
        self.assertNotIn(self.oauth_task_id, session)
        self.assertNotIn(self.faces_task_key, session)

    def test_failed_none(self, celery_mock):
        task = celery_mock.current_app.AsyncResult.return_value
        task.ready.return_value = True
        task.successful.return_value = True
        task.result = None
        response = self.client.get(self.url)
        self.assertStatusCode(response, 200)
        self.assertEqual(len(task.method_calls), 2)
        session = self.client.session
        self.assertNotIn(self.oauth_task_id, session)
        self.assertNotIn(self.faces_task_key, session)

    @patch('targetshare.views.faces.request_targeting')
    def test_already_started(self, targeting_mock, celery_mock):
        task = celery_mock.current_app.AsyncResult.return_value
        task.ready.return_value = True
        task.successful.return_value = True
        task.result = models.datastructs.ShortToken(1, 1, 'TOKZ', '1.0')

        targeting_mock.return_value = ((3, Mock(id='PX3-2')), (4, Mock(id='PX4-2')))

        self.session[self.faces_task_key] = targeting_task_ids = [[3, 'PX3-1'], [4, 'PX4-1']]
        self.session.save()

        response = self.client.get(self.url)
        self.assertStatusCode(response, 200)
        self.assertEqual(len(task.method_calls), 2)

        session = self.client.session
        self.assertNotIn(self.oauth_task_id, session)
        self.assertEqual(session[self.faces_task_key], targeting_task_ids)

        self.assertFalse(targeting_mock.called)

    @patch('targetshare.views.faces.request_targeting')
    def test_eager_targeting(self, targeting_mock, celery_mock):
        task = celery_mock.current_app.AsyncResult.return_value
        task.ready.return_value = True
        task.successful.return_value = True
        task.result = token = models.datastructs.ShortToken(1, 1, 'TOKZ', '1.0')

        targeting_mock.return_value = ((3, Mock(id='PX3-2')), (4, Mock(id='PX4-2')))

        response = self.client.get(self.url)
        self.assertStatusCode(response, 200)
        self.assertEqual(len(task.method_calls), 2)

        session = self.client.session
        self.assertNotIn(self.oauth_task_id, session)
        self.assertEqual(session[self.faces_task_key], [[3, 'PX3-2'], [4, 'PX4-2']])

        self.assertTrue(targeting_mock.called)
        targeting_mock.assert_called_once_with(
            api=1,
            token=token,
            visit=models.Visit.objects.get(session_id=session.session_key),
            campaign=models.Campaign.objects.get(pk=1),
            client_content=models.ClientContent.objects.get(pk=1),
            num_faces=10,
        )
