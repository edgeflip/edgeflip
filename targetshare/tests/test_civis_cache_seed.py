import json
from datetime import datetime, timedelta

from mock import patch, Mock
from boto.exception import S3ResponseError
from django.core.management.base import CommandError

from targetshare import models
from targetshare import mock_facebook
from targetshare.management.commands import civis_cache_seed

from . import EdgeFlipTestCase


class TestCivisCacheSeed(EdgeFlipTestCase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestCivisCacheSeed, self).setUp()
        self.orig_facebook = civis_cache_seed.facebook
        civis_cache_seed.facebook = mock_facebook

        self.command = civis_cache_seed.Command()
        self.command.client = models.Client.objects.get()
        self.command.filter = self.command.client.filters.all()[0]
        self.command.cache_age = datetime.now() - timedelta(days=10)
        self.command.s3_conn = Mock()
        self.command.bucket = Mock()

        self.uc = models.UserClient.objects.create(
            client=self.command.client,
            fbid=123456
        )
        self.token = models.Token(
            fbid=123456,
            token='fake-token',
            appid=self.command.client.fb_app_id
        )
        self.token.save(overwrite=True)
        self.civis_result = {
            u'123456': {
                u'error': False,
                u'result': {u'more_people': False,
                u'people': [{u'TokenCount': 6,
                        u'birth_day': u'01',
                        u'birth_month': u'12',
                        u'birth_year': u'1969',
                        u'city': u'CHARLOTTESVILLE',
                        u'dma': u'584',
                        u'dma_name': u'Charlottesville VA',
                        u'first_name': u'TEST',
                        u'gender': u'M',
                        u'id': u'16595385',
                        u'last_name': u'USER',
                        u'nick_name': u'TESTUSER',
                        u'scores': {
                            u'gotv_score': 0,
                            u'persuasion_score': 25.59,
                            u'persuasion_score_dec': 3,
                            u'support_cand_2013': 52.085,
                            u'support_cand_2013_dec': 7,
                            u'turnout_2013': 85.419,
                            u'turnout_2013_dec': 9},
                        u'state': u'VA'}],
                u'people_count': 1,
                u'scores': {
                    u'gotv_score': {
                        u'count': 1,
                        u'max': 23.592,
                        u'mean': 23.592,
                        u'min': 23.592,
                        u'std': 0
                    },
                    u'persuasion_score': {
                        u'count': 1,
                        u'max': 17.161,
                        u'mean': 17.161,
                        u'min': 17.161,
                        u'std': 0
                    }
                }}
            }
        }

    def tearDown(self):
        civis_cache_seed.facebook = self.orig_facebook
        super(TestCivisCacheSeed, self).tearDown()

    @patch('targetshare.management.commands.civis_cache_seed.boto')
    def test_handle_method(self, boto_mock):
        ''' Test the ensures the handle method behaves appropriately '''
        methods_to_mock = [
            '_get_bucket',
            '_retrieve_users',
            '_perform_matching',
            '_store_match_results'
        ]
        pre_mocks = []
        for method in methods_to_mock:
            pre_mocks.append(getattr(self.command, method))
            setattr(self.command, method, Mock())

        self.command.handle(1, 1, days=5, bucket='testing')
        for count, method in enumerate(methods_to_mock):
            assert getattr(self.command, method).called
            setattr(self.command, method, pre_mocks[count])

    def test_handle_method_invalid_args(self):
        ''' Tests the civis_cache_seed command being called with invalid
        arguments
        '''
        with self.assertRaises(CommandError):
            # No args, no dice
            self.command.handle()

        with self.assertRaises(CommandError):
            # 1 arg, still not good enough
            self.command.handle(1)

    def test_retrieve_users(self):
        ''' Test the user retrieval method of the command '''
        users = self.command._retrieve_users()
        # Should only have one valid user
        self.assertEqual(len(users), 1)
        assert users[0] # Assert we have edges

    def test_get_bucket_failure(self):
        ''' Test the S3 bucket retrieval failure '''
        self.command.s3_conn.get_bucket.side_effect = S3ResponseError('o', 'w')
        self.command.s3_conn.create_bucket.side_effect = S3ResponseError('oh', 'no')
        self.command.stderr = Mock()
        with self.assertRaises(S3ResponseError):
            self.command._get_bucket('bad bucket')

        assert self.command.stderr.write.called

    def test_get_bucket_success(self):
        ''' Test a successful bucket retrieval '''
        self.command.s3_conn.get_bucket.return_value = 'mrbucket_rocks'
        self.assertEqual(
            self.command._get_bucket('mrbucket'),
            'mrbucket_rocks'
        )

    @patch('civis_matcher.matcher.requests.post')
    def test_perform_matching(self, requests_mock):
        ''' Tests the _perform_matching method '''
        requests_mock.return_value = Mock(
            status_code=200,
            url='http://example.com/test-failure',
            content=json.dumps(self.civis_result)
        )
        users = self.command._retrieve_users()
        # Give our primary some legit data
        users[0][0].primary.city = 'Chicago'
        users[0][0].primary.state = 'Illinois'
        matches = self.command._perform_matching(users)
        assert matches['123456']
        self.assertEqual(matches['123456']['result']['people_count'], 1)

    def test_store_match_results_new_key(self):
        ''' Tests the _store_match_results method with a new key'''
        self.command.bucket = Mock()
        self.command.bucket.get_key.return_value = None
        create_key_mock = Mock()
        self.command.bucket.new_key.return_value = create_key_mock
        self.command._store_match_results(self.civis_result)
        assert create_key_mock.set_contents_from_string.called
        store_data = json.loads(
            create_key_mock.set_contents_from_string.call_args_list[0][0][0]
        )
        self.assertEqual(
            store_data['result'],
            self.civis_result['123456']['result']
        )

    def test_store_match_results_existing_key(self):
        ''' Test of the result storage where we update an existing key '''
        self.command.bucket = Mock()
        key_mock = Mock()
        key_data = self.civis_result.copy()
        key_data['timestamp'] = (datetime.now() - timedelta(days=100)).strftime(
            civis_cache_seed.TIME_FORMAT
        )
        key_mock.get_contents_as_string.return_value = json.dumps(key_data)
        self.command.bucket.get_key.return_value = key_mock
        self.command._store_match_results(self.civis_result)
        assert key_mock.get_contents_as_string.called
        assert key_mock.set_contents_from_string.called

    def test_store_match_results_key_too_fresh(self):
        ''' Test result storage where an object is found to be new enough to be
        trusted
        '''
        self.command.bucket = Mock()
        key_mock = Mock()
        key_data = self.civis_result.copy()
        key_data['123456']['timestamp'] = datetime.now().strftime(
            civis_cache_seed.TIME_FORMAT
        )
        key_mock.get_contents_as_string.return_value = json.dumps(
            key_data['123456']
        )
        self.command.bucket.get_key.return_value = key_mock
        self.command._store_match_results(self.civis_result)
        assert key_mock.get_contents_as_string.called
        assert not key_mock.set_contents_from_string.called
