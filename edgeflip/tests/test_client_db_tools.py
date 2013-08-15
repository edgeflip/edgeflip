import json
from datetime import date

from mock import Mock, patch

from edgeflip.tests import EdgeFlipTestCase
from edgeflip import (
    client_db_tools as cdb,
    datastructs,
)
import copy


class TestClientDBTools(EdgeFlipTestCase):

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

        user = datastructs.UserInfo(
            1, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', 'Illinois'
        )
        edge = datastructs.Edge(user, user, None)
        result = cdb.civisFilter([edge], 'persuasion_score', 'min', 10)
        self.assertEqual(result, [edge])

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
        user = datastructs.UserInfo(
            1, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', 'Illinois'
        )
        edge = datastructs.Edge(user, user, None)
        result = cdb.civisFilter([edge], 'persuasion_score', 'min', 100)
        self.assertEqual(result, [])

    @patch('civis_matcher.matcher.requests.post')
    def test_filter_by_edges_sec(self, requests_mock):
        ''' Tests Filter.filterEdgesBySec, and thus acts more like an actual
        integration test
        '''
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
        filter_obj = cdb.Filter(1, [('persuasion_score', 'min', 10)])
        user = datastructs.UserInfo(
            1, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', 'Illinois'
        )
        edge = datastructs.Edge(user, user, None)
        result = filter_obj.filterEdgesBySec([edge])
        self.assertEqual(result, [edge])

    def test_tiered_edges(self):

        test_user1 = datastructs.UserInfo(
            uid=1,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            sex='male',
            birthday=date(1984, 1, 1),
            city='Chicago',
            state='Illinois',
        )
        test_user2 = copy.deepcopy(test_user1)
        test_user2.id = 2
        test_user3 = copy.deepcopy(test_user1)
        test_user3.id = 3
        test_user4 = copy.deepcopy(test_user1)
        test_user4.id = 4

        test_edge1 = datastructs.Edge(
            test_user1,
            test_user1,
            None
        )
        test_edge2 = datastructs.Edge(
            test_user1,
            test_user2,
            None
        )
        test_edge3 = datastructs.Edge(
            test_user1,
            test_user3,
            None
        )
        test_edge4 = datastructs.Edge(
            test_user1,
            test_user4,
            None
        )

        edgesFiltered = cdb.TieredEdges(edges=[test_edge1], campaignId=1)
        edgesFiltered.appendTier(edges=[test_edge4, test_edge3], campaignId=7)
        edgesFiltered.appendTier(edges=[test_edge2], campaignId=3)

        self.assertEqual(len(edgesFiltered), 4)
        self.assertEqual(edgesFiltered.secondaryIds(), [1, 4, 3, 2])
        assert all([isinstance(x, datastructs.Edge) for x in edgesFiltered.edges()])
        assert all([isinstance(x, datastructs.UserInfo) for x in edgesFiltered.secondaries()])

        px4_edges = [test_edge3, test_edge2, test_edge4, test_edge1]
        edgesFiltered.rerankEdges(px4_edges)

        self.assertEqual(edgesFiltered.secondaryIds(), [1, 3, 4, 2])

        px5_edges = [test_edge4, test_edge2]
        edgesFiltered.rerankEdges(px5_edges)

        self.assertEqual(len(edgesFiltered), 4)
        self.assertEqual(edgesFiltered.secondaryIds(), [1, 4, 3, 2])
