from datetime import date

from mock import Mock, patch

from edgeflip.tests import EdgeFlipTestCase
from edgeflip import (
    client_db_tools as cdb,
    datastructs,
)
import copy


class TestClientDBTools(EdgeFlipTestCase):

    def setUp(self):
        super(TestClientDBTools, self).setUp()
        self.test_user1 = datastructs.UserInfo(
            uid=1,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            sex='male',
            birthday=date(1984, 1, 1),
            city='Chicago',
            state='Illinois',
        )
        self.test_user2 = copy.deepcopy(self.test_user1)
        self.test_user2.id = 2
        self.test_user3 = copy.deepcopy(self.test_user1)
        self.test_user3.id = 3
        self.test_user4 = copy.deepcopy(self.test_user1)
        self.test_user4.id = 4

        self.test_edge1 = datastructs.Edge(
            self.test_user1,
            self.test_user1,
            None
        )
        self.test_edge2 = datastructs.Edge(
            self.test_user1,
            self.test_user2,
            None
        )
        self.test_edge3 = datastructs.Edge(
            self.test_user1,
            self.test_user3,
            None
        )
        self.test_edge4 = datastructs.Edge(
            self.test_user1,
            self.test_user4,
            None
        )

    @patch('edgeflip.client_db_tools.matcher')
    def test_civis_matching_match_found(self, civis_mock):
        ''' Test the civis matching task where a match is found '''
        matcher_mock = Mock()
        matcher_mock.match.return_value = Mock(scores=
            {
                'persuasion_score': {
                    'min': 100
                }
            }
        )
        civis_mock.CivisMatcher.return_value = matcher_mock
        user = datastructs.UserInfo(
            1, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', 'Illinois'
        )
        edge = datastructs.Edge(user, user, None)
        matches = []
        cdb.civisFilter(edge, 'persuasion_score', 'min', 100, matches)
        self.assertEqual([edge], matches)

    @patch('edgeflip.client_db_tools.matcher')
    def test_civis_matching_no_match(self, civis_mock):
        ''' Test the civis matching task where a match is not found '''
        matcher_mock = Mock()
        matcher_mock.match.return_value = Mock(scores=
            {
                'persuasion_score': {
                    'min': 10
                }
            }
        )
        civis_mock.CivisMatcher.return_value = matcher_mock
        user = datastructs.UserInfo(
            1, u'Test', u'User', 'test@example.com', 'Male',
            date(1984, 1, 1), u'Chicago', 'Illinois'
        )
        edge = datastructs.Edge(user, user, None)
        matches = []
        cdb.civisFilter(edge, 'persuasion_score', 'min', 100, matches)
        self.assertEqual(matches, [])

    def test_tiered_edges(self):
        edgesFiltered = cdb.TieredEdges('campaignId', 1, [self.test_edge1])
        edgesFiltered.appendTier(7, [self.test_edge4, self.test_edge3])
        edgesFiltered.appendTier(3, [self.test_edge2])

        self.assertEqual(len(edgesFiltered), 4)
        self.assertEqual(edgesFiltered.secondaryIds(), [1, 4, 3, 2])
        assert all([isinstance(x, datastructs.Edge) for x in edgesFiltered.edges()])
        assert all([isinstance(x, datastructs.UserInfo) for x in edgesFiltered.secondaries()])

        px4_edges = [self.test_edge3, self.test_edge2, self.test_edge4, self.test_edge1]
        edgesFiltered.rerankEdges(px4_edges)

        self.assertEqual(edgesFiltered.secondaryIds(), [1, 3, 4, 2])

        px5_edges = [self.test_edge4, self.test_edge2]
        edgesFiltered.rerankEdges(px5_edges)

        self.assertEqual(len(edgesFiltered), 4)
        self.assertEqual(edgesFiltered.secondaryIds(), [1, 4, 3, 2])
