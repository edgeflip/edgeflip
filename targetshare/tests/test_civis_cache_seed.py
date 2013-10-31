import json
from datetime import datetime, timedelta

from mock import patch, Mock

from targetshare import models
from targetshare.management.commands import civis_cache_seed

from . import EdgeFlipTestCase, patch_facebook


class TestCivisCacheSeed(EdgeFlipTestCase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestCivisCacheSeed, self).setUp()

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

    @patch_facebook
    def test_handle_method(self):
        ''' Test the ensures the handle method behaves appropriately '''
        methods_to_mock = [
            '_retrieve_users',
            '_perform_matching',
        ]
        pre_mocks = []
        for method in methods_to_mock:
            pre_mocks.append(getattr(self.command, method))
            setattr(self.command, method, Mock())

        self.command.handle(1, days=5, bucket='testing')
        for count, method in enumerate(methods_to_mock):
            assert getattr(self.command, method).called
            setattr(self.command, method, pre_mocks[count])

    @patch_facebook
    def test_retrieve_users(self):
        ''' Test the user retrieval method of the command '''
        users = self.command._retrieve_users()
        edges = users.next()
        assert edges
        with self.assertRaises(StopIteration):
            users.next()

    @patch_facebook
    @patch('civis_matcher.matcher.requests.post')
    @patch('civis_matcher.matcher.S3CivisMatcher._get_bucket')
    def test_perform_matching(self, get_bucket_mock, requests_mock):
        ''' Tests the _perform_matching method '''
        requests_mock.return_value = Mock(
            status_code=200,
            url='http://example.com/test',
            content=json.dumps(self.civis_result)
        )
        bucket_mock = Mock()
        bucket_mock.get_key.return_value = None
        get_bucket_mock.return_value = bucket_mock
        self.command.days = 30
        users = self.command._retrieve_users()
        self.command._perform_matching(users)
        match = models.CivisResult.items.get_item(fbid=123456)
        data = json.loads(match['result'])
        self.assertEqual(data['result']['people_count'], 1)
