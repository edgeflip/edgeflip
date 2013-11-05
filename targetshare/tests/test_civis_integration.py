import json
from datetime import datetime

from django.utils import timezone
from mock import Mock, patch

from targetshare import models
from targetshare.integration.civis import client

from . import EdgeFlipTestCase


class TestCivisIntegration(EdgeFlipTestCase):

    fixtures = ['test_data']

    @patch('civis_matcher.matcher.requests.post')
    def test_civis_matching_match_found(self, requests_mock):
        ''' Test the civis matching task where a match is found '''
        requests_mock.return_value = Mock(
            status_code=200,
            url='http://example.com/test-failure',
            content=json.dumps({
                u'1': {
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
            })
        )

        user = models.User(
            fbid=1, fname=u'Test', lname=u'User', email='test@example.com', gender='Male',
            birthday=timezone.make_aware(datetime(1984, 1, 1), timezone.utc),
            city=u'Chicago', state='Illinois'
        )
        edge = models.datastructs.Edge(user, user, None)
        result = client.civis_filter([edge], 'persuasion_score', 'min', 10)
        self.assertEqual(result, [edge])

    @patch('civis_matcher.matcher.requests.post')
    def test_civis_matching_no_score_key(self, requests_mock):
        """ Test the civis matching task where a match is found, but we
        receive data without the filter_feature key we're expecting
        """
        requests_mock.return_value = Mock(
            status_code=200,
            url='http://example.com/test-failure',
            content=json.dumps({
                u'1': {
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
            })
        )

        user = models.User(
            fbid=1, fname=u'Test', lname=u'User', email='test@example.com', gender='Male',
            birthday=timezone.make_aware(datetime(1984, 1, 1), timezone.utc),
            city=u'Chicago', state='Illinois'
        )
        edge = models.datastructs.Edge(user, user, None)
        result = client.civis_filter([edge], 'persuasion_score_bogus', 'min', 10)
        self.assertEqual(result, [])

    @patch('civis_matcher.matcher.requests.post')
    def test_civis_matching_no_match(self, requests_mock):
        ''' Test the civis matching task where a match is not found '''
        requests_mock.return_value = Mock(
            status_code=200,
            url='http://example.com/test-failure',
            content=json.dumps({
                u'1': {
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
            })
        )
        user = models.User(
            fbid=1, fname=u'Test', lname=u'User', email='test@example.com', gender='Male',
            birthday=timezone.make_aware(datetime(1984, 1, 1), timezone.utc),
            city=u'Chicago', state='Illinois'
        )
        edge = models.datastructs.Edge(user, user, None)
        result = client.civis_filter([edge], 'persuasion_score', 'min', 100)
        self.assertEqual(result, [])
