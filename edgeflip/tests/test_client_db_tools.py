from datetime import date

from mock import Mock, patch

from edgeflip.tests import EdgeFlipTestCase
from edgeflip import (
    client_db_tools as cdb,
    datastructs,
)


class TestClientDBTools(EdgeFlipTestCase):

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
        matches = []
        cdb.civisFilter(user, 'persuasion_score', 100, matches)
        self.assertEqual([user], matches)

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
        matches = []
        cdb.civisFilter(user, 'persuasion_score', 100, matches)
        self.assertEqual(matches, [])
