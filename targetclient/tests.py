import datetime

from freezegun import freeze_time
from mock import patch

from targetshare.models.dynamo import Token
from targetshare.tests import EdgeFlipTestCase

from targetclient.models import OFAToken
from targetclient.management.commands import synctokens


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
        self.assertIn('database, model and appid required', message)

    def test_ofa(self):
        self.assertEqual(OFAToken.objects.count(), 3)
        self.assertEqual(Token.items.count(), 0)

        self.command.run_from_argv([
            'manage.py',
            'synctokens',
            '--database=default',
            '--model=OFAToken',
            '--appid=10101',
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

    def test_ofa_filter(self):
        self.assertEqual(OFAToken.objects.count(), 3)
        self.assertEqual(Token.items.count(), 0)

        self.command.run_from_argv([
            'manage.py',
            'synctokens',
            '--database=default',
            '--model=OFAToken',
            '--appid=10101',
            '--since=2014-01-01',
        ])
        tokens = Token.items.scan()

        (token,) = tokens
        self.assertEqual(token.fbid, 2)

    def test_ofa_filter_interval(self):
        self.assertEqual(OFAToken.objects.count(), 3)
        self.assertEqual(Token.items.count(), 0)

        self.command.run_from_argv([
            'manage.py',
            'synctokens',
            '--database=default',
            '--model=OFAToken',
            '--appid=10101',
            '--since=60d',
        ])
        tokens = Token.items.scan()

        (token,) = tokens
        self.assertEqual(token.fbid, 2)
