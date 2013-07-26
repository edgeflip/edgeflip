import datetime
import types
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

    updated = datetime.datetime(2013, 1, 1) + datetime.timedelta(days=-1)

    def everyone(self):
        """helper that returns some user dicts. map of fbid => dict of user data"""
        return {u['fbid']: u for u in
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
        assert isinstance(x, dict)

        self.assertEqual(x['fbid'], 1234)
        self.assertEqual(x['birthday'], datetime.date(1950, 1, 1))
        self.assertEqual(x['email'], 'alice@example.com')
        self.assertEqual(x['gender'], 'Female')
        self.assertNotIn('city', x)
        self.assertNotIn('state', x)

    def test_save_many_users(self):
        """Test saving many users"""
        dynamo.save_many_users(self.everyone().values())
        table = dynamo.get_table('users')

        results = list(table.batch_get(keys=[{'fbid':k} for k in self.everyone().keys()]))
        self.assertItemsEqual([x['fbid'] for x in results], self.everyone().keys())

        for x in results:
            d = dict(x.items())
            user = self.everyone().get(x['fbid'])
            dynamo._remove_null_values(user)

            # munge the raw dict from dynamo in a compatible way
            assert 'updated' in d
            del d['updated']
            d['fbid'] = int(d['fbid'])
            if 'birthday' in d:
                d['birthday'] = dynamo.epoch_to_date(d.get('birthday'))

            self.assertDictEqual(user, d)

    def test_fetch_many_users(self):
        """Test fetching many users"""
        dynamo.save_many_users(self.everyone().values())
        users = list(dynamo.fetch_many_users(self.everyone().keys()))
        for u in users:
            self.assertIsInstance(u, dict)
            assert 'updated' in u
            del u['updated']

            d = self.everyone()[u['fbid']]
            for k, v in d.items():
                if isinstance(v, (types.NoneType, basestring, set, list, tuple)) and not v:
                    del d[k]

            self.assertDictEqual(u, d)


@freeze_time('2013-01-01')
class DynamoTokenTestCase(EdgeFlipTestCase):

    expiry = datetime.datetime(2014, 01, 01)

    def tokens(self):
        """helper that returns some tokens data, keyed by (fbid, appid)"""
        return {(x['fbid'], x['appid']): x for x in
                [
                    dict(fbid=1234, appid=666, token="FOOD1111",
                         expires=datetime.datetime(2014, 01, 01)),

                    dict(fbid=1234, appid=42, token="FOOD2222",
                         expires=datetime.datetime(2014, 02, 02)),

                    dict(fbid=5678, appid=666, token="FOOD5555",
                         expires=datetime.datetime(2014, 02, 02)),

                ]}

    def save_token(self):
        """helper to save a single token, DECAFBAD"""
        dynamo.save_token(1234, 666, 'DECAFBAD', self.expiry)

    def test_save_token(self):
        """Test saving a new token"""
        self.save_token()

        table = dynamo.get_table('tokens')
        x = table.get_item(fbid=1234, appid=666)
        self.assertEqual(x['fbid'], 1234)
        self.assertEqual(x['appid'], 666)
        self.assertEqual(x['token'], 'DECAFBAD')
        self.assertEqual(x['expires'], dynamo.datetime_to_epoch(self.expiry))
        assert 'updated' in x

    def test_save_token_update(self):
        """Test updating a token - overwrites"""
        self.save_token()

        # update token
        dynamo.save_token(1234, 666, 'FADEDCAB', self.expiry)

        table = dynamo.get_table('tokens')
        x = table.get_item(fbid=1234, appid=666)
        self.assertEqual(x['token'], 'FADEDCAB')

    def test_fetch_token(self):
        """Test fetching an existing token"""
        self.save_token()

        x = dynamo.fetch_token(1234, 666)
        assert isinstance(x, dict)
        assert 'updated' in x
        del x['updated']

        self.assertEqual(x['fbid'], 1234)
        self.assertEqual(x['appid'], 666)
        self.assertEqual(x['token'], 'DECAFBAD')
        self.assertEqual(x['expires'], self.expiry)


    def test_fetch_many_tokens(self):
        """Test fetching many tokens"""

        for d in self.tokens().values():
            dynamo.save_token(**d)

        tokens = list(dynamo.fetch_many_tokens(self.tokens().keys()))

        for t in tokens:
            assert isinstance(t, dict)
            del t['updated']
            d = self.tokens()[(t['fbid'], t['appid'])]

            self.assertDictEqual(t, d)