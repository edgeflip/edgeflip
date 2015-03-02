import re

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from targetshare.models import relational

from chapo import models


URL = "http://www.reddit.com/r/food/"


class TestRedirectService(TestCase):

    def setUp(self):
        self.short = models.ShortenedUrl.objects.create(url=URL)
        self.path = reverse('chapo:main', args=[self.short.slug])

    def test_post(self):
        """el chapo does not accept POSTs"""
        response = self.client.post(self.path)
        self.assertEqual(response.status_code, 405)

    def test_put(self):
        """el chapo does not accept PUTs (without authorization)"""
        response = self.client.put(self.path)
        self.assertEqual(response.status_code, 401)

    def test_delete(self):
        """el chapo does not accept DELETEs"""
        response = self.client.delete(self.path)
        self.assertEqual(response.status_code, 405)

    def test_get_not_found(self):
        """el chapo returns 404s for unknown aliases"""
        self.short.delete()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 404)

    def test_get(self):
        """el chapo returns 301s with content for GETs"""
        response = self.client.get(self.path)
        anchor = """<a href="{0}">{0}</a>""".format(URL)
        self.assertContains(response, anchor, count=1, status_code=301, html=True)
        self.assertEqual(response['Location'], URL)

    def test_head(self):
        """el chapo returns 301s without content for HEADs"""
        response = self.client.head(self.path)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.content, '')
        self.assertEqual(response['Location'], URL)


class TestJavaScriptRedirectService(TestCase):

    def setUp(self):
        self.short = models.ShortenedUrl.objects.create(url=URL)
        self.path = reverse('chapo:html', args=[self.short.slug])

    def test_get(self):
        """el chapo returns HTML with a JavaScript redirect"""
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)

        template = r'''<script.+outgoingRedirect\(['"]{URL}['"]\);.*</script>'''
        snippet = template.format(URL=re.escape(URL))
        regexp = re.compile(snippet, re.DOTALL)
        self.assertRegexpMatches(response.content, regexp)


class RedirectCampaignTestCase(TestCase):

    fixtures = ('test_data',)

    def setUp(self):
        self.campaign = relational.Campaign.objects.all()[0]
        self.short = self.campaign.shortenedurls.create(event_type='initial_redirect', url=URL)
        self.path = reverse('chapo:main', args=[self.short.slug])

        self.events = relational.Event.objects.all()
        self.visits = relational.Visit.objects.all()

        self.assertEqual(self.events.count(), 0)
        self.assertEqual(self.visits.count(), 0)


class TestRedirectCampaign(RedirectCampaignTestCase):

    def test_redirect_event(self):
        """el chapo records an event"""
        response = self.client.get(self.path)

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], URL)

        visit = self.visits.get()
        event_values = self.events.values('event_type', 'campaign_id', 'client_content',
                                          'content', 'friend_fbid', 'activity_id')

        self.assertEqual(visit.session_id, self.client.cookies['sessionid'].value)
        self.assertEqual({event.visit for event in self.events}, {visit})
        self.assertEqual({event.event_type for event in self.events},
                         {'session_start', 'initial_redirect'})
        self.assertEqual(event_values.get(event_type='initial_redirect'), {
            'event_type': 'initial_redirect',
            'campaign_id': self.campaign.pk,
            'client_content': None,
            'content': self.short.slug,
            'friend_fbid': None,
            'activity_id': None,
        })

    def test_cycle_session(self):
        """el chapo starts a new visit"""
        # Force an initial session
        self.client.cookies[settings.SESSION_COOKIE_NAME] = 'fake'
        session = self.client.session
        session['willi'] = 'beretained?'
        session.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        # Create a visitor and visit for this session
        visitor = relational.Visitor.objects.create()
        visit0 = visitor.visits.create(
            session_id=session.session_key,
            app_id=self.campaign.client.fb_app_id,
            ip='127.0.0.1',
        )
        self.client.cookies[settings.VISITOR_COOKIE_NAME] = visitor.uuid

        self.assertEqual(self.events.count(), 0)
        self.assertEqual(self.visits.count(), 1)

        response = self.client.get(self.path)

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], URL)

        # Check new session & visit
        self.assertEqual(self.visits.count(), 2)
        visit = visitor.visits.exclude(pk=visit0.pk).get() # visitor retained
        self.assertEqual(visit.session_id, self.client.session.session_key)
        self.assertNotEqual(visit.session_id, visit0.session_id)

        self.assertEqual(self.events.count(), 2)
        self.assertEqual(sorted(visit.events.values_list('event_type', flat=True)),
                         ['initial_redirect', 'session_start'])

        # Check session data retained
        self.assertIn('willi', self.client.session)
        self.assertEqual(self.client.session['willi'], 'beretained?')


class TestDraftCampaign(RedirectCampaignTestCase):

    def setUp(self):
        super(TestDraftCampaign, self).setUp()
        self.campaign.campaignproperties.update(
            status=relational.CampaignProperties.Status.DRAFT,
        )

        self.user = User.objects.create_user('mockuser', password='1234')
        self.group = self.user.groups.create(name='mockgroup')

    def test_not_authenticated(self):
        response = self.client.get(self.path)
        self.assertContains(response, "Page under construction", status_code=403)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'preview_denied',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })

    def test_not_authorized(self):
        logged_in = self.client.login(username='mockuser', password='1234')
        self.assertTrue(logged_in)

        response = self.client.get(self.path)
        self.assertContains(response, "Page under construction", status_code=403)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'preview_denied',
            'campaign_id': 1,
            'content': 'mockuser',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })

    def test_authorized(self):
        self.campaign.client.auth_groups.add(self.group)

        logged_in = self.client.login(username='mockuser', password='1234')
        self.assertTrue(logged_in)

        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], URL)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'client_preview',
            'campaign_id': 1,
            'content': 'mockuser',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })


class TestInactiveCampaign(RedirectCampaignTestCase):

    def setUp(self):
        super(TestInactiveCampaign, self).setUp()
        self.campaign.campaignproperties.update(
            status=relational.CampaignProperties.Status.INACTIVE,
        )

        self.user = User.objects.create_user('mockuser', password='1234')
        self.group = self.user.groups.create(name='mockgroup')

        self.inactive_url = 'http://localhost/phooey'
        outgoing_path = reverse('outgoing', args=[self.campaign.client.fb_app_id,
                                                  self.inactive_url])
        self.outgoing_path = "{}?campaignid={}".format(outgoing_path, self.campaign.campaign_id)
        self.outgoing_url = "http://testserver" + self.outgoing_path
        self.final_url = self.inactive_url + "?rs=ef1"

    def test_not_authenticated(self):
        response = self.client.get(self.path)
        self.assertContains(response, "Page removed", status_code=410)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'inactive_campaign',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })

    def test_not_authorized(self):
        logged_in = self.client.login(username='mockuser', password='1234')
        self.assertTrue(logged_in)

        response = self.client.get(self.path)
        self.assertContains(response, "Page removed", status_code=410)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'inactive_campaign',
            'campaign_id': 1,
            'content': 'mockuser',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })

    def test_not_authenticated_campaign_redirect(self):
        self.campaign.campaignproperties.update(inactive_url=self.inactive_url)

        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.outgoing_url)

        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.final_url)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 5)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'inactive_campaign',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[3], {
            'event_type': 'outgoing_redirect',
            'campaign_id': 1,
            'content': self.final_url,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[4], {
            'event_type': 'cookies_enabled',
            'campaign_id': None,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })

    def test_not_authorized_campaign_redirect(self):
        logged_in = self.client.login(username='mockuser', password='1234')
        self.assertTrue(logged_in)

        self.campaign.campaignproperties.update(inactive_url=self.inactive_url)

        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.outgoing_url)

        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.final_url)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 5)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'inactive_campaign',
            'campaign_id': 1,
            'content': 'mockuser',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[3], {
            'event_type': 'outgoing_redirect',
            'campaign_id': 1,
            'content': self.final_url,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[4], {
            'event_type': 'cookies_enabled',
            'campaign_id': None,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })

    def test_not_authenticated_client_redirect(self):
        self.campaign.client.campaign_inactive_url = self.inactive_url
        self.campaign.client.save()

        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.outgoing_url)

        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.final_url)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 5)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'inactive_campaign',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[3], {
            'event_type': 'outgoing_redirect',
            'campaign_id': 1,
            'content': self.final_url,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[4], {
            'event_type': 'cookies_enabled',
            'campaign_id': None,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })

    def test_not_authorized_client_redirect(self):
        logged_in = self.client.login(username='mockuser', password='1234')
        self.assertTrue(logged_in)

        self.campaign.client.campaign_inactive_url = self.inactive_url
        self.campaign.client.save()

        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.outgoing_url)

        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.final_url)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 5)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'inactive_campaign',
            'campaign_id': 1,
            'content': 'mockuser',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[3], {
            'event_type': 'outgoing_redirect',
            'campaign_id': 1,
            'content': self.final_url,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[4], {
            'event_type': 'cookies_enabled',
            'campaign_id': None,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })

    def test_authorized(self):
        self.campaign.client.auth_groups.add(self.group)

        logged_in = self.client.login(username='mockuser', password='1234')
        self.assertTrue(logged_in)

        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Page removed", response.content)
        self.assertIn("This campaign has been archived and may no longer be accessed", response.content)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'inactive_campaign',
            'campaign_id': 1,
            'content': 'mockuser',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })

    def test_authorized_campaign_redirect(self):
        self.campaign.client.auth_groups.add(self.group)

        logged_in = self.client.login(username='mockuser', password='1234')
        self.assertTrue(logged_in)

        self.campaign.campaignproperties.update(inactive_url=self.inactive_url)

        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Page removed", response.content)
        self.assertIn("This campaign has been archived and may no longer be accessed", response.content)
        self.assertIn(self.outgoing_path, response.content)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'inactive_campaign',
            'campaign_id': 1,
            'content': 'mockuser',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })

    def test_authorized_client_redirect(self):
        self.campaign.client.auth_groups.add(self.group)

        logged_in = self.client.login(username='mockuser', password='1234')
        self.assertTrue(logged_in)

        self.campaign.client.campaign_inactive_url = self.inactive_url
        self.campaign.client.save()

        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Page removed", response.content)
        self.assertIn("This campaign has been archived and may no longer be accessed", response.content)
        self.assertIn(self.outgoing_path, response.content)

        visit = self.visits.get()
        events = visit.events.order_by('event_datetime', 'pk').values(
            'event_type', 'campaign_id', 'client_content',
            'content', 'friend_fbid', 'activity_id'
        )

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], {
            'event_type': 'session_start',
            'campaign_id': 1,
            'content': '',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[1], {
            'event_type': 'initial_redirect',
            'campaign_id': 1,
            'content': self.short.slug,
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
        self.assertEqual(events[2], {
            'event_type': 'inactive_campaign',
            'campaign_id': 1,
            'content': 'mockuser',
            'client_content': None,
            'friend_fbid': None,
            'activity_id': None,
        })
