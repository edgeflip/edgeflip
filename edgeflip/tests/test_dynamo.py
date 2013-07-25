import datetime
from freezegun import freeze_time

from edgeflip.tests import EdgeFlipTestCase
from edgeflip import (
    dynamo,
    datastructs
)

def test_remove_null_values():
    '''test internal _remove_null_values'''
    good = {"string": 'wat',
            "num": 9000,
            "zero": 0,
            "set": set([1, 2, 3]),
            "dict": dict(foo=42),
            }
    good_ = good.copy()
    dynamo._remove_null_values(good_)
    assert good_ == good, good_

    bad = {"string": '',
            "set": set(),
            "dict": {},
            }
    bad_ = bad.copy()
    dynamo._remove_null_values(bad_)
    assert bad_ == {}

@freeze_time('2013-01-01')
class DynamoUserTestCase(EdgeFlipTestCase):

    def save_alice(self):
        """helper to save a single user alice"""
        dynamo.save_user(1234, 'Alice', 'Apples', 'alice@example.com', 'Female', datetime.date(1950, 1, 1), None, '')

    def test_save_user_new(self):
        """Test saving a new user"""
        self.save_alice()

        table = dynamo.get_table('users')
        x = table.get_item(fbid=1234)
        self.assertEqual(x['fname'], 'Alice')
        self.assertEqual(x['fbid'], 1234)
        self.assertEqual(x['birthday'], -631130400)
        self.assertEqual(x['updated'], 1357020000)
        self.assertIsNone(x['city'])
        self.assertIsNone(x['state'])

    def test_save_user_update(self):
        """Test updating an existing user"""
        self.save_alice()

        # update alice
        dynamo.save_user(1234, 'Alice', 'Apples', None, 'Female', None, 'Anchorage', 'AK')

        table = dynamo.get_table('users')
        x = table.get_item(fbid=1234)
        self.assertEqual(x['fname'], 'Alice')
        self.assertEqual(x['fbid'], 1234)
        self.assertEqual(x['city'], 'Anchorage')
        self.assertEqual(x['state'], 'AK')

