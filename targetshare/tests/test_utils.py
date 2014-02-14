from django.utils import unittest

from targetshare import utils


class TestPartition(unittest.TestCase):

    def test_numbers(self):
        parts = utils.partition([85, 70, 50, 40, 40, 25, 3, 2],
                                range_width=30,
                                max_value=100)
        self.assertSequenceEqual(
            # w/o min_value, must iterate over group on each loop
            [(bound, list(group)) for (bound, group) in parts],
            [(70, [85, 70]), (40, [50, 40, 40]), (10, [25]), (-20, [3, 2])]
        )

    def test_numbers_natural_max(self):
        parts = utils.partition([85, 70, 50, 40, 40, 25, 3, 2], range_width=30)
        self.assertSequenceEqual(
            # w/o min_value, must iterate over group on each loop
            [(bound, list(group)) for (bound, group) in parts],
            [(55, [85, 70]), (25, [50, 40, 40, 25]), (-5, [3, 2])]
        )

    def test_numbers_min(self):
        parts = utils.partition([85, 70, 50, 40, 40, 25, 3, 2],
                                range_width=30,
                                min_value=0,
                                max_value=100)
        # with min_value, may iterate over partitions eagerly
        (bounds, groups) = zip(*parts)
        self.assertSequenceEqual(bounds, [70, 40, 10, -20])
        self.assertSequenceEqual([list(group) for group in groups], (
            [85, 70], [50, 40, 40], [25], [3, 2]))

    def test_numbers_min_natural_max(self):
        parts = utils.partition([85, 70, 50, 40, 40, 25, 3, 2],
                                range_width=30,
                                min_value=0)
        # with min_value, may iterate over partitions eagerly
        (bounds, groups) = zip(*parts)
        self.assertSequenceEqual(bounds, [55, 25, -5])
        self.assertSequenceEqual([list(group) for group in groups], (
            [85, 70], [50, 40, 40, 25], [3, 2]))
