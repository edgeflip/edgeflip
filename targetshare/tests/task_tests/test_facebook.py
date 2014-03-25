import json
from datetime import datetime

import mock
from freezegun import freeze_time
from faraday.utils import epoch

from targetshare import models
from targetshare.tasks.integration import facebook

from .. import EdgeFlipTestCase


requests_patch = mock.patch('requests.get', **{'return_value.content': 'access_token=TOKZ'})

urllib2_patch = mock.patch('urllib2.urlopen', **{'return_value.read.return_value': json.dumps({
    'data': {
        'is_valid': True,
        'user_id': 100,
        'expires_at': epoch.from_date(datetime(2013, 5, 15, 12, 1, 1)),
    }
})})


@freeze_time('2013-01-01')
class TestStoreOpenAuthToken(EdgeFlipTestCase):

    fixtures = ('test_data',)

    @requests_patch
    @urllib2_patch
    def test_store_auth(self, urllib_mock, requests_mock):
        user_clients = models.UserClient.objects.filter(fbid=100, client_id=1)
        tokens = models.Token.items.filter(fbid__eq=100, appid__eq=471727162864364)
        self.assertEqual(user_clients.count(), 0)
        self.assertEqual(tokens.query_count(), 0)
        facebook.store_oauth_token(1, 'PIEZ', 'http://testserver/incoming/SLUGZ/')
        self.assertEqual(user_clients.count(), 1)
        self.assertEqual(tokens.query_count(), 1)

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
