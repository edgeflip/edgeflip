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

    # some user dicts. map of fbid => dict of user data
    everyone = {u['fbid']: u for u in
                [
                    dict(fbid=1234, fname='Alice', lname='Apples', email='alice@example.com',
                         gender='Female', birthday=datetime.date(1950, 1, 1), city=None, state=''),

                    dict(fbid=100, fname='Bob', lname='Beet', email='bob@example.com',
                         gender=None, birthday=None, city=None, state=None),

                    dict(fbid=101, fname='Carol', lname='Corn', email='carol@example.com',
                         gender='Female', birthday=datetime.date(1980, 1, 1), city='Compton', state='CA'),

                    dict(fbid=102, fname='David', lname='Dill', email='david@example.com',
                         gender='Male', birthday=None, city=None, state='DE'),
                ]}


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

    def test_fetch_user(self):
        """Test fetching an existing user"""
        self.save_alice()

        x = dynamo.fetch_user(1234)
        assert isinstance(x, datastructs.UserInfo)

        self.assertEqual(x.id, 1234)
        self.assertEqual(x.birthday, datetime.date(1950, 1, 1))
        self.assertEqual(x.email, 'alice@example.com')
        self.assertEqual(x.gender, 'Female')
        self.assertIsNone(x.city)
        self.assertIsNone(x.state)

    def test_save_many_users(self):
        """Test saving many users"""
        dynamo.save_many_users(self.everyone.values())
        table = dynamo.get_table('users')

        results = list(table.batch_get(keys=[{'fbid':k} for k in self.everyone.keys()]))
        self.assertItemsEqual([x['fbid'] for x in results], self.everyone.keys())

        for x in results:
            d = dict(x.items())
            u = self.everyone.get(x['fbid']).copy()
            dynamo._remove_null_values(u)
            self.assertDictEqual(d, u)


