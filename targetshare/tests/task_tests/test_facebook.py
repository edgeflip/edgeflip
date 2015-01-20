import json
import urllib
from datetime import datetime, timedelta

import mock
from freezegun import freeze_time
from faraday.utils import epoch

from targetshare import models
from targetshare.tasks.integration import facebook

from .. import EdgeFlipTestCase


DEBUG_TOKEN_MOCK = json.dumps({
    'data': {
        'is_valid': True,
        'user_id': 100,
        'expires_at': epoch.from_date(datetime(2013, 5, 15, 12, 1, 1)),
    }
})

EXTEND_TOKEN_MOCK = urllib.urlencode([
    ('access_token', 'tok1'),
    ('expires', str(60 * 60 * 24 * 60)), # 60 days in seconds
])


@freeze_time('2013-01-01')
class TestStoreOpenAuthToken(EdgeFlipTestCase):

    fixtures = ('test_data',)

    requests_patch = mock.patch('requests.get', **{'return_value.content': 'access_token=TOKZ'})

    urllib2_patch = mock.patch('urllib2.urlopen', **{'return_value.read.side_effect': [
        DEBUG_TOKEN_MOCK,
        EXTEND_TOKEN_MOCK,
    ]})

    @requests_patch
    @urllib2_patch
    def test_store_auth(self, urllib_mock, requests_mock):
        user_clients = models.UserClient.objects.filter(fbid=100, client_id=1)
        tokens = models.Token.items.filter(fbid__eq=100, appid__eq=471727162864364)
        self.assertEqual(user_clients.count(), 0)
        self.assertEqual(tokens.query_count(), 0)

        token = facebook.store_oauth_token(1, 'PIEZ', 'http://testserver/incoming/SLUGZ/')

        self.assertEqual(token, (100, 471727162864364, 'TOKZ'))
        self.assertEqual(user_clients.count(), 1)
        self.assertEqual(tokens.query_count(), 1)
        extended_token = tokens.filter_get()
        self.assertEqual(extended_token.fbid, 100)
        self.assertEqual(extended_token.token, 'tok1')

    @requests_patch
    @mock.patch('urllib2.urlopen', **{'return_value.read.return_value': json.dumps({
        'data': {'is_valid': False}
    })})
    def test_invalid_token(self, urllib_mock, requests_mock):
        user_clients = models.UserClient.objects.filter(fbid=100, client_id=1)
        tokens = models.Token.items.filter(fbid__eq=100, appid__eq=471727162864364)
        facebook.store_oauth_token(1, 'PIEZ', 'http://testserver/incoming/SLUGZ/')
        self.assertEqual(user_clients.count(), 0)
        self.assertEqual(tokens.query_count(), 0)

    @requests_patch
    @urllib2_patch
    def test_record_auth(self, urllib_mock, requests_mock):
        client = models.Client.objects.get(pk=1)
        user_clients = client.userclients.filter(fbid=100)
        tokens = models.Token.items.filter(fbid__eq=100, appid__eq=471727162864364)
        visitor = models.Visitor.objects.create()
        visit = visitor.visits.create(session_id='sid001', app_id=client.fb_app_id, ip='0.0.0.0')

        facebook.store_oauth_token(client.pk, 'PIEZ', 'http://testserver/incoming/SLUGZ/', visit.pk)
        self.assertEqual(user_clients.count(), 1)
        self.assertEqual(tokens.query_count(), 1)

        auths = visit.events.filter(event_type='authorized')
        self.assertEqual(len(auths), 1)
        (auth,) = auths
        self.assertEqual(auth.content, 'oauth')
        self.assertIsNone(auth.campaign_id)
        self.assertEqual(auth.visit, visit)

        visitor = models.Visitor.objects.get(visits__visit_id=auth.visit_id) # refresh
        self.assertEqual(visitor, visit.visitor)
        self.assertEqual(visitor.fbid, 100)

    @requests_patch
    @urllib2_patch
    def test_record_auth_meta(self, urllib_mock, requests_mock):
        client = models.Client.objects.get(pk=1)
        user_clients = client.userclients.filter(fbid=100)
        tokens = models.Token.items.filter(fbid__eq=100, appid__eq=471727162864364)
        visitor = models.Visitor.objects.create()
        visit = visitor.visits.create(session_id='sid001', app_id=client.fb_app_id, ip='0.0.0.0')

        facebook.store_oauth_token(client.pk, 'PIEZ', 'http://testserver/incoming/SLUGZ/',
                                   visit_id=visit.pk, campaign_id=1, content_id=1)
        self.assertEqual(user_clients.count(), 1)
        self.assertEqual(tokens.query_count(), 1)

        auths = visit.events.filter(event_type='authorized')
        self.assertEqual(len(auths), 1)
        (auth,) = auths
        self.assertEqual(auth.content, 'oauth')
        self.assertEqual(auth.campaign_id, 1)
        self.assertEqual(auth.client_content_id, 1)
        self.assertEqual(auth.visit, visit)

        visitor = models.Visitor.objects.get(visits__visit_id=auth.visit_id) # refresh
        self.assertEqual(visitor, visit.visitor)
        self.assertEqual(visitor.fbid, 100)

    @requests_patch
    @urllib2_patch
    def test_visitor_switch(self, urllib_mock, requests_mock):
        client = models.Client.objects.get(pk=1)
        user_clients = client.userclients.filter(fbid=100)
        tokens = models.Token.items.filter(fbid__eq=100, appid__eq=471727162864364)
        visitor = models.Visitor.objects.create(fbid=222)
        visit = visitor.visits.create(session_id='sid001', app_id=client.fb_app_id, ip='0.0.0.0')

        facebook.store_oauth_token(client.pk, 'PIEZ', 'http://testserver/incoming/SLUGZ/', visit.pk)
        self.assertEqual(user_clients.count(), 1)
        self.assertEqual(tokens.query_count(), 1)

        auths = visit.events.filter(event_type='authorized')
        self.assertEqual(len(auths), 1)
        (auth,) = auths
        self.assertEqual(auth.content, 'oauth')
        self.assertIsNone(auth.campaign_id)

        visitor = models.Visitor.objects.get(visits__visit_id=auth.visit_id) # refresh
        self.assertEqual(auth.visit, visit)
        self.assertNotEqual(visitor, visit.visitor)
        self.assertEqual(visitor.fbid, 100)

    @requests_patch
    @urllib2_patch
    def test_visitor_match(self, urllib_mock, requests_mock):
        client = models.Client.objects.get(pk=1)
        user_clients = client.userclients.filter(fbid=100)
        tokens = models.Token.items.filter(fbid__eq=100, appid__eq=471727162864364)
        visitor = models.Visitor.objects.create(fbid=100)
        visit = visitor.visits.create(session_id='sid001', app_id=client.fb_app_id, ip='0.0.0.0')

        facebook.store_oauth_token(client.pk, 'PIEZ', 'http://testserver/incoming/SLUGZ/', visit.pk)
        self.assertEqual(user_clients.count(), 1)
        self.assertEqual(tokens.query_count(), 1)

        auths = visit.events.filter(event_type='authorized')
        self.assertEqual(len(auths), 1)
        (auth,) = auths
        self.assertEqual(auth.content, 'oauth')
        self.assertIsNone(auth.campaign_id)

        visitor = models.Visitor.objects.get(visits__visit_id=auth.visit_id) # refresh
        self.assertEqual(auth.visit, visit)
        self.assertEqual(visitor, visit.visitor)
        self.assertEqual(visitor.fbid, 100)

    @requests_patch
    @urllib2_patch
    def test_existing_visitor(self, urllib_mock, requests_mock):
        client = models.Client.objects.get(pk=1)
        user_clients = client.userclients.filter(fbid=100)
        tokens = models.Token.items.filter(fbid__eq=100, appid__eq=471727162864364)
        existing_visitor = models.Visitor.objects.create(fbid=100)
        visitor = models.Visitor.objects.create()
        visit = visitor.visits.create(session_id='sid001', app_id=client.fb_app_id, ip='0.0.0.0')

        facebook.store_oauth_token(client.pk, 'PIEZ', 'http://testserver/incoming/SLUGZ/', visit.pk)
        self.assertEqual(user_clients.count(), 1)
        self.assertEqual(tokens.query_count(), 1)

        auths = visit.events.filter(event_type='authorized')
        self.assertEqual(len(auths), 1)
        (auth,) = auths
        self.assertEqual(auth.content, 'oauth')
        self.assertIsNone(auth.campaign_id)

        visitor = models.Visitor.objects.get(visits__visit_id=auth.visit_id) # refresh
        self.assertEqual(auth.visit, visit)
        self.assertNotEqual(visitor, visit.visitor)
        self.assertEqual(visitor, existing_visitor)
        self.assertEqual(visitor.fbid, 100)


class TestExtendToken(EdgeFlipTestCase):

    urllib2_patch = mock.patch('urllib2.urlopen', **{'return_value.read.return_value': EXTEND_TOKEN_MOCK})

    @urllib2_patch
    def test_extension(self, _urllib_mock):
        models.relational.FBApp.objects.create(
            appid=471727162864364,
            name='Share!',
            secret='sekret',
        )
        tokens = models.Token.items.filter(fbid__eq=100, appid__eq=471727162864364)
        self.assertEqual(tokens.query_count(), 0)

        now = epoch.utcnow()
        facebook.extend_token(100, 471727162864364, 'xyz')

        token = tokens.filter_get()
        self.assertEqual(token.token, 'tok1')
        self.assertAlmostEqual(token.expires, now + timedelta(days=60),
                               delta=timedelta(seconds=1))
