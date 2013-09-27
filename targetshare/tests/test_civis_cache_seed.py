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
            '_retrieve_users',
            '_perform_matching',
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

    @patch('civis_matcher.matcher.requests.post')
    @patch('civis_matcher.matcher.S3CivisMatcher._get_bucket')
    @patch('civis_matcher.matcher.boto')
    def test_perform_matching(self, boto_mock, get_bucket_mock, requests_mock):
        ''' Tests the _perform_matching method '''
        requests_mock.return_value = Mock(
            status_code=200,
            url='http://example.com/test',
            content=json.dumps(self.civis_result)
        )
        bucket_mock = Mock()
        bucket_mock.get_key.return_value = None
        get_bucket_mock.return_value = bucket_mock
        users = self.command._retrieve_users()
        # Give our primary some legit data
        users[0][0].primary.city = 'Chicago'
        users[0][0].primary.state = 'Illinois'
        matches = self.command._perform_matching(users)
        assert matches['123456']
        self.assertEqual(matches['123456']['result']['people_count'], 1)
