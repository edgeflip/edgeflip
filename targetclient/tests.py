import datetime
from django.utils import timezone
import json
from requests import exceptions
import time

from freezegun import freeze_time
from mock import patch, Mock

from targetshare.models.dynamo import Token
from targetshare.models.relational import UserClient
from targetshare.tests import EdgeFlipTestCase

from targetclient.models import OFAToken
from targetclient.management.commands import ensure_users_from_tokens, synctokens
from targetclient import tasks


@freeze_time('2014-02-14')
class TestSyncTokens(EdgeFlipTestCase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestSyncTokens, self).setUp()
        self.command = synctokens.Command()

    @patch('django.core.management.base.OutputWrapper')
    def test_missing_parameter(self, _wrapper_mock):
        self.assertRaises(SystemExit, self.command.run_from_argv, [
            'manage.py',
            'synctokens',
        ])
        self.assertTrue(self.command.stderr.write.called)
        (call,) = self.command.stderr.write.call_args_list
        ((message,), _kws) = call
        self.assertIn('database, model and clientid required', message)

    def test_ofa(self):
        original_user_clients = UserClient.objects.count()
        self.assertEqual(OFAToken.objects.count(), 3)
        self.assertEqual(Token.items.count(), 0)

        client_id = 1

        self.command.run_from_argv([
            'manage.py',
            'synctokens',
            '--database=default',
            '--model=OFAToken',
            '--clientid={}'.format(client_id),
        ])
        tokens = Token.items.scan()

        self.assertEqual(len(tokens), 2)

        (expires,) = {token.expires for token in tokens}
        self.assertEqual(expires.date(), datetime.date(2014, 4, 15))

        ignore = ('expires', 'updated')
        token_data = (
            {
                key: value for (key, value) in token.items()
                if key not in ignore
            }
            for token in tokens
        )
        sorted_data = sorted(token_data, key=lambda data: data['fbid'])
        self.assertEqual(sorted_data, [
            {
                'fbid': 1,
                'token': '02i3jndiskjddfwssa',
                'appid': 10101,
            },
            {
                'fbid': 2,
                'token': 't2a3j1diskjddfwssa',
                'appid': 10101,
            },
        ])

        self.assertEqual(UserClient.objects.count() - original_user_clients, 2)
        self.assertEqual(UserClient.objects.get(fbid=1).client_id, client_id)
        self.assertEqual(UserClient.objects.get(fbid=2).client_id, client_id)

    def test_ofa_filter(self):
        self.assertEqual(OFAToken.objects.count(), 3)
        self.assertEqual(Token.items.count(), 0)

        self.command.run_from_argv([
            'manage.py',
            'synctokens',
            '--database=default',
            '--model=OFAToken',
            '--clientid=1',
            '--since=2014-01-01',
        ])
        tokens = Token.items.scan()

        (token,) = tokens
        self.assertEqual(token.fbid, 2)

    @patch('targetclient.management.commands.synctokens.get_db_now')
    def test_ofa_filter_interval(self, db_now_mock):
        db_now_mock.return_value = datetime.datetime(2014, 2, 14)
        self.assertEqual(OFAToken.objects.count(), 3)
        self.assertEqual(Token.items.count(), 0)

        self.command.run_from_argv([
            'manage.py',
            'synctokens',
            '--database=default',
            '--model=OFAToken',
            '--clientid=1',
            '--since=60d',
        ])
        tokens = Token.items.scan()

        (token,) = tokens
        self.assertEqual(token.fbid, 2)


@freeze_time('2014-03-17')
class TestEnsureUsersFromTokens(EdgeFlipTestCase):

    fixtures = ['test_client_data']

    def setUp(self):
        super(TestEnsureUsersFromTokens, self).setUp()
        self.command = ensure_users_from_tokens.Command()
        self.synced_fbid = 123
        self.visited_fbid = 456
        self.appid = 10101
        self.client_id = 1
        self.the_past = timezone.now() - datetime.timedelta(days=5)
        self.the_future = timezone.now() + datetime.timedelta(days=5)
        self.synced_token = Token(fbid=self.synced_fbid, appid=self.appid, token='1', expires=self.the_future)
        self.synced_token.save()
        self.visited_token = Token(fbid=self.visited_fbid, appid=self.appid, token='1', expires=self.the_past)
        self.visited_token.save()


    def test_ensure_user_client(self):
        new_expires_ts = time.time()
        new_expires_obj = timezone.make_aware(datetime.datetime.utcfromtimestamp(new_expires_ts), timezone.utc)
        with patch(
            'targetshare.integration.facebook.client.debug_token',
            Mock(
                return_value=json.dumps({
                    'data': {
                        'expires_at': new_expires_ts,
                        'app_id': self.appid,
                        'user_id': self.synced_fbid,
                        'application': 'This organization',
                    },
                })
            )
        ):
            queryset = UserClient.objects.filter(fbid__in=[self.visited_fbid, self.synced_fbid], client_id=1)
            self.assertEqual(queryset.count(), 0)

            self.command.execute()
            self.assertEqual(queryset.count(), 2)
            self.assertEqual(Token.items.get_item(fbid=self.synced_fbid, appid=self.appid).expires, new_expires_obj)
            self.assertEqual(Token.items.get_item(fbid=self.visited_fbid, appid=self.appid).expires, self.the_past)

            # don't put in duplicates
            self.command.execute()
            self.assertEqual(queryset.count(), 2)


    @patch('django.core.management.base.OutputWrapper')
    def test_ensure_user_client_exception(self, output_wrapper):
        with patch(
            'targetshare.integration.facebook.client.debug_token',
            side_effect=exceptions.RequestException
        ):
            self.command.execute()
            self.assertEqual(Token.items.get_item(fbid=self.visited_fbid, appid=self.appid).expires, self.the_past)
            self.assertEqual(Token.items.get_item(fbid=self.synced_fbid, appid=self.appid).expires, self.the_future)

        self.assertTrue(self.command.stderr.write.called)


    @patch('django.core.management.base.OutputWrapper')
    def test_ensure_user_client_bad_data(self, output_wrapper):
        with patch(
            'targetshare.integration.facebook.client.debug_token',
            Mock(return_value='not json')
        ):
            self.command.execute()
            self.assertEqual(Token.items.get_item(fbid=self.visited_fbid, appid=self.appid).expires, self.the_past)
            self.assertEqual(Token.items.get_item(fbid=self.synced_fbid, appid=self.appid).expires, self.the_future)
        self.assertTrue(self.command.stderr.write.called)

