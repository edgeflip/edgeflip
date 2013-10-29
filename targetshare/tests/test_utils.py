import json
from datetime import datetime

from mock import Mock, patch

from django.utils import timezone, unittest

from targetshare import models, utils

from . import EdgeFlipTestCase


class TestLazySequence(unittest.TestCase):

    get_sequence = utils.LazySequence

    def test_lazy_init(self):
        iterable = iter([1, 2])
        seq = self.get_sequence(iterable)
        self.assertTrue(seq.iterable)
        self.assertFalse(list(seq._results.__iter__()))
        self.assertEqual(list(iterable), [1, 2])

    def test_init_len(self):
        seq = self.get_sequence([1, 2])
        self.assertEqual(len(seq), 2)
        self.assertIsNone(seq.iterable)
        self.assertEqual(list(seq._results.__iter__()), [1, 2])
        self.assertItemsEqual(seq, [1, 2])

    def test_bool_false(self):
        seq = self.get_sequence()
        self.assertFalse(seq)

    def test_bool_true_lazy(self):
        seq = self.get_sequence([1, 2])
        self.assertTrue(seq)
        self.assertTrue(seq.iterable)
        self.assertEqual(list(seq._results.__iter__()), [1])

    def test_lazy_len(self):
        seq = self.get_sequence([1, 2])
        self.assertTrue(seq)
        self.assertEqual(len(seq), 2)
        self.assertIsNone(seq.iterable)
        self.assertItemsEqual(seq, [1, 2])

    def test_getitem_lazy(self):
        seq = self.get_sequence([1, 2, 3])
        self.assertEqual(seq[1], 2)
        self.assertTrue(seq.iterable)
        self.assertEqual(list(seq._results.__iter__()), [1, 2])

    def test_getslice_lazy(self):
        seq = self.get_sequence([1, 2, 3])
        sliced = seq[:2]
        self.assertIsNot(sliced, seq)
        self.assertItemsEqual(sliced, [1, 2])
        self.assertTrue(seq.iterable)
        self.assertEqual(list(seq._results.__iter__()), [1, 2])

    def test_count(self):
        iterable = iter([1, 2, 2, 2])
        seq = self.get_sequence(iterable)
        self.assertEqual(seq.count(2), 3)
        self.assertFalse(list(iterable))

    def test_index_preexisting(self):
        iterable = iter([1, 2, 2, 2])
        seq = self.get_sequence(iterable)
        self.assertEqual(seq[1], 2)
        self.assertEqual(seq.index(2), 1)

    def test_index_advance(self):
        iterable = iter([1, 2, 2, 2])
        seq = self.get_sequence(iterable)
        self.assertEqual(seq.index(2), 1)

    def test_index_missing(self):
        seq = self.get_sequence([1, 2, 2, 2])
        with self.assertRaises(ValueError):
            seq.index(5)

    def test_contains_preexisting(self):
        iterable = iter([1, 2, 2, 2])
        seq = self.get_sequence(iterable)
        self.assertEqual(seq[2], 2)
        self.assertIn(2, seq)
        self.assertTrue(seq.iterable)
        self.assertEqual(list(iterable), [2])

    def test_contains_advance(self):
        iterable = iter([1, 2, 2, 2])
        seq = self.get_sequence(iterable)
        self.assertIn(2, seq)
        self.assertTrue(seq.iterable)
        self.assertEqual(list(iterable), [2, 2])

    def test_ladd(self):
        seq = self.get_sequence([1, 2])
        result = seq + [3, 4]
        self.assertTrue(seq.iterable)
        self.assertTrue(result.iterable)
        self.assertEqual(list(result), [1, 2, 3, 4])

    def test_radd(self):
        seq = self.get_sequence([1, 2])
        result = [3, 4] + seq
        self.assertIsNone(seq.iterable)
        self.assertEqual(result, [3, 4, 1, 2])
        self.assertItemsEqual(seq, [1, 2])

    def test_mul(self):
        seq = self.get_sequence([1, 2])
        result = seq * 2
        self.assertTrue(result.iterable)
        self.assertTrue(seq.iterable)
        self.assertItemsEqual(result, [1, 2, 1, 2])
        self.assertItemsEqual(seq, [1, 2])


class TestLazyList(TestLazySequence):

    # Inherits tests from parent!
    get_sequence = utils.LazyList

    def test_setslice_lazy(self):
        iterable = iter([1, 2, 3, 4])
        seq = self.get_sequence(iterable)
        seq[1:3] = (8, 9)
        self.assertTrue(seq.iterable)
        self.assertEqual(list(iterable), [4])
        self.assertItemsEqual(seq, [1, 8, 9])

    def test_delslice_lazy(self):
        iterable = iter([1, 2, 3, 4])
        seq = self.get_sequence(iterable)
        del seq[0:2]
        self.assertTrue(seq.iterable)
        self.assertEqual(list(iterable), [3, 4])
        self.assertFalse(seq)

    def test_extend_lazy(self):
        seq = self.get_sequence([1, 2])
        seq.extend([3, 4])
        self.assertEqual(seq._results.__len__(), 0)
        self.assertItemsEqual(seq, [1, 2, 3, 4])

    def test_extend_eager(self):
        seq = self.get_sequence([1, 2])
        self.assertItemsEqual(seq, [1, 2])
        seq.extend([3, 4])
        self.assertEqual(seq._results.__len__(), 4)
        self.assertItemsEqual(seq, [1, 2, 3, 4])

    def test_insert_lazy(self):
        seq = self.get_sequence(['a', 'c'])
        seq.insert(1, 'b')
        self.assertItemsEqual(seq._results.__iter__(), ['a', 'b'])
        self.assertItemsEqual(seq, ['a', 'b', 'c'])

    def test_pop_lazy(self):
        seq = self.get_sequence(['a', 'b', 'c'])
        self.assertEqual(seq.pop(1), 'b')
        self.assertItemsEqual(seq._results.__iter__(), ['a'])
        self.assertItemsEqual(seq, ['a', 'c'])

    def test_remove_lazy(self):
        seq = self.get_sequence(['a', 'b', 'c'])
        seq.remove('b')
        self.assertItemsEqual(seq._results.__iter__(), ['a'])
        self.assertItemsEqual(seq, ['a', 'c'])

    def test_reverse(self):
        seq = self.get_sequence(['a', 'b', 'c'])
        seq.reverse()
        self.assertIsNone(seq.iterable)
        self.assertItemsEqual(seq, ['c', 'b', 'a'])

    def test_sort(self):
        seq = self.get_sequence([10, 0, 'a'])
        seq.sort(key=lambda item: str(item))
        self.assertIsNone(seq.iterable)
        self.assertItemsEqual(seq, [0, 10, 'a'])


class TestCivisMatching(EdgeFlipTestCase):

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
        result = utils.civis_filter([edge], 'persuasion_score', 'min', 10)
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
        result = utils.civis_filter([edge], 'persuasion_score_bogus', 'min', 10)
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
        result = utils.civis_filter([edge], 'persuasion_score', 'min', 100)
        self.assertEqual(result, [])
