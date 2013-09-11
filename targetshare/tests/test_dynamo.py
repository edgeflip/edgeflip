import datetime
import types

from django.utils import timezone
from freezegun import freeze_time
from nose import tools

from targetshare.models import dynamo

from . import EdgeFlipTestCase


def test_remove_null_values():
    '''test internal _remove_null_values'''
    good = {"string": 'wat',
            "num": 9000,
            "zero": 0,
            "set": {1, 2, 3},
            "dict": {'foo': 42}}
    good_ = good.copy()
    dynamo.db._remove_null_values(good_)
    tools.eq_(good_, good)

    bad = {"string": '',
           "set": set(),
           "dict": {}}
    bad_ = bad.copy()
    dynamo.db._remove_null_values(bad_)
    tools.eq_(bad_, {})


class TestDynamo(EdgeFlipTestCase):

    def test_batching(self):
        """batch_get continues even if one batch empty"""
        # Provision two users:
        with dynamo.User.items.batch_write() as batch:
            for fbid in (100, 101):
                data = {'fbid': fbid}
                # put_item should accept either dict or Item:
                if fbid % 2:
                    data = dynamo.User(data)
                batch.put_item(data)

        # Request users s.t. first batch of 100 don't exist:
        keys = [{'fbid': count} for count in xrange(102)]
        users = dynamo.User.items.batch_get(keys=keys)
        self.assertEqual(sum(1 for user in users), 2)


@freeze_time('2013-01-01')
class DynamoUserTestCase(EdgeFlipTestCase):

    updated = datetime.datetime(2013, 1, 1, tzinfo=timezone.utc) + datetime.timedelta(days=-1)

    def users(self):
        """helper that returns some user dicts. map of fbid => dict of user data"""
        return {u['fbid']: u for u in
                [
                    dict(fbid=1234, fname='Alice', lname='Apples', email='alice@example.com',
                         gender='Female', birthday=datetime.datetime(1950, 1, 1, tzinfo=timezone.utc), city=None, state=''),

                    dict(fbid=100, fname='Bob', lname='Beet', email='bob@example.com',
                         gender=None, birthday=None, city=None, state=None),

                    dict(fbid=101, fname='Carol', lname='Corn', email='carol@example.com',
                         gender='Female', birthday=datetime.datetime(1980, 1, 1, tzinfo=timezone.utc), city='Compton', state='CA'),

                    dict(fbid=102, fname='David', lname='Dill', email='david@example.com',
                         gender='Male', birthday=None, city=None, state='DE'),
                ]}

    def save_alice(self):
        """helper to save a single user alice"""
        dynamo.db.save_user(1234, 'Alice', 'Apples', 'alice@example.com', 'Female', datetime.datetime(1950, 1, 1, tzinfo=timezone.utc), None, '')

    def save_users(self):
        with dynamo.User.items.batch_write() as batch:
            for user in self.users().values():
                batch.put_item(user)

    def test_save_user_new(self):
        """Test saving a new user"""
        self.save_alice()

        table = dynamo.db.get_table('users')
        x = table.get_item(fbid=1234)
        self.assertEqual(x['fname'], 'Alice')
        self.assertEqual(x['fbid'], 1234)
        self.assertEqual(x['birthday'], -631152000)
        self.assertEqual(x['updated'], 1356998400)
        self.assertIsNone(x['city'])
        self.assertIsNone(x['state'])

    def test_save_user_update(self):
        """Test updating an existing user"""
        self.save_alice()

        # update alice
        dynamo.db.save_user(1234, 'Alice', 'Apples', None, 'Female', None, 'Anchorage', 'AK')

        table = dynamo.db.get_table('users')
        x = table.get_item(fbid=1234)
        self.assertEqual(x['fname'], 'Alice')
        self.assertEqual(x['fbid'], 1234)
        self.assertEqual(x['city'], 'Anchorage')
        self.assertEqual(x['state'], 'AK')

    def test_fetch_user(self):
        """Test fetching an existing user"""
        self.save_alice()

        x = dynamo.db.fetch_user(1234)
        assert isinstance(x, dict)

        self.assertEqual(x['fbid'], 1234)
        self.assertEqual(x['birthday'], datetime.datetime(1950, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(x['email'], 'alice@example.com')
        self.assertEqual(x['gender'], 'Female')
        self.assertNotIn('city', x)
        self.assertNotIn('state', x)

    def test_save_many_users(self):
        self.save_users()

        users = self.users()
        keys = [{'fbid': key} for key in users]
        results = tuple(dynamo.User.items.batch_get(keys=keys))
        self.assertItemsEqual((item['fbid'] for item in results), users)

        for item in results:
            data = dict(item)
            user = self.users()[item['fbid']]

            # Munge data to be comparable:
            dynamo.db._remove_null_values(user)
            data['fbid'] = int(data['fbid'])
            data.pop('updated')

            self.assertDictEqual(data, user)

    def test_fetch_many_users(self):
        """Test fetching many users"""
        self.save_users()
        users = list(dynamo.db.fetch_many_users(self.users().keys()))
        for u in users:
            self.assertIsInstance(u, dict)
            assert 'updated' in u
            del u['updated']

            d = self.users()[u['fbid']]
            for k, v in d.items():
                if isinstance(v, (types.NoneType, basestring, set, list, tuple)) and not v:
                    del d[k]

            self.assertDictEqual(u, d)


@freeze_time('2013-01-01')
class DynamoTokenTestCase(EdgeFlipTestCase):

    expiry = datetime.datetime(2014, 01, 01, tzinfo=timezone.utc)

    def tokens(self):
        """helper that returns some tokens data, keyed by (fbid, appid)"""
        return {(x['fbid'], x['appid']): x for x in
                [
                    dict(fbid=1234, appid=666, token="FOOD1111",
                         expires=datetime.datetime(2014, 01, 01, tzinfo=timezone.utc)),

                    dict(fbid=1234, appid=42, token="FOOD2222",
                         expires=datetime.datetime(2014, 02, 02, tzinfo=timezone.utc)),

                    dict(fbid=5678, appid=666, token="FOOD5555",
                         expires=datetime.datetime(2014, 02, 02, tzinfo=timezone.utc)),

                ]}

    def save_token(self, fbid=1234, appid=666, token='DECAFBAD'):
        """helper to save a single token, DECAFBAD"""
        token = dynamo.Token(fbid=fbid, appid=appid, token=token, expires=self.expiry)
        token.save(overwrite=True)
        return token

    def test_save_token(self):
        """Test saving a new token"""
        self.save_token()

        table = dynamo.db.get_table('tokens')
        x = table.get_item(fbid=1234, appid=666)
        self.assertEqual(x['fbid'], 1234)
        self.assertEqual(x['appid'], 666)
        self.assertEqual(x['token'], 'DECAFBAD')
        self.assertEqual(x['expires'], dynamo.db.to_epoch(self.expiry))
        assert 'updated' in x

    def test_save_token_update(self):
        """Test updating a token - overwrites"""
        self.save_token()
        self.save_token(token='FADEDCAB')
        token = dynamo.Token.items.get_item(fbid=1234, appid=666)
        self.assertEqual(token['token'], 'FADEDCAB')

    def test_fetch_token(self):
        """Test fetching an existing token"""
        self.save_token()

        x = dynamo.db.fetch_token(1234, 666)
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
            dynamo.Token.items.put_item(d)

        tokens = list(dynamo.db.fetch_many_tokens(self.tokens().keys()))

        for t in tokens:
            assert isinstance(t, dict)
            del t['updated']
            d = self.tokens()[(t['fbid'], t['appid'])]
            self.assertDictEqual(t, d)


@freeze_time('2013-01-01')
class DynamoEdgeTestCase(EdgeFlipTestCase):

    expiry = datetime.datetime(2014, 01, 01, tzinfo=timezone.utc)

    maxDiff = 1000

    def edges(self):
        """helper that returns some edges data, keyed by (fbid_target, fbid_source)"""
        return {(x['fbid_source'], x['fbid_target']): x for x in [

            dict(fbid_source=100, fbid_target=200, post_likes=42, post_comms=18,
                 stat_likes=None, stat_comms=None, wall_posts=0, wall_comms=10,
                 tags=86, photos_target=None, photos_other=None, mut_friends=200),

            dict(fbid_source=101, fbid_target=200, post_likes=None, post_comms=None,
                 stat_likes=50, stat_comms=55, wall_posts=138, wall_comms=None,
                 tags=None, photos_target=6, photos_other=4, mut_friends=101),

            dict(fbid_source=100, fbid_target=202, post_likes=80, post_comms=65,
                 stat_likes=4, stat_comms=44, wall_posts=10, wall_comms=100,
                 tags=22, photos_target=23, photos_other=24, mut_friends=202),

            dict(fbid_source=500, fbid_target=600, post_likes=None, post_comms=None,
                 stat_likes=102, stat_comms=88, wall_posts=None, wall_comms=None,
                 tags=None, photos_target=33, photos_other=44, mut_friends=600),

            dict(fbid_source=500, fbid_target=601, post_likes=1, post_comms=2,
                 stat_likes=3, stat_comms=4, wall_posts=5, wall_comms=6,
                 tags=6, photos_target=8, photos_other=9, mut_friends=601),
        ]}

    def save_edge(self):
        """helper to save a single edge, (100, 200)"""
        dynamo.db.save_edge(**self.edges()[(100, 200)])

    def test_save_edge(self):
        """Test saving a new edge"""
        self.save_edge()

        incoming = dynamo.db.get_table('edges_incoming')
        x = incoming.get_item(fbid_source=100, fbid_target=200)
        assert 'updated' in x
        del x['updated']
        d = dict(x.items())

        e = self.edges()[(100, 200)]
        dynamo.db._remove_null_values(e)
        self.assertDictEqual(d, e)

        outgoing = dynamo.db.get_table('edges_outgoing')
        x = outgoing.get_item(fbid_source=100, fbid_target=200)
        assert 'updated' in x
        del x['updated']
        d = dict(x.items())
        self.assertDictEqual(d, dict(fbid_source=100, fbid_target=200))

    def test_save_token_update(self):
        """Test updating a edge - overwrites"""
        self.save_edge()

        e = self.edges()[(100, 200)]

        e['stat_likes'] = 9000
        e['stat_comms'] = 9001
        e['tags'] = None
        # update edge
        dynamo.db.save_edge(**e)

        incoming = dynamo.db.get_table('edges_incoming')
        x = incoming.get_item(fbid_source=100, fbid_target=200)
        assert 'updated' in x
        del x['updated']
        d = dict(x.items())

        e['tags'] = 86 # unchanged, we don't overwrite w/ None/0
        dynamo.db._remove_null_values(e)
        self.assertDictEqual(d, e)

        outgoing = dynamo.db.get_table('edges_outgoing')
        x = outgoing.get_item(fbid_source=100, fbid_target=200)
        assert 'updated' in x
        del x['updated']
        d = dict(x.items())
        self.assertDictEqual(d, dict(fbid_source=100, fbid_target=200))

    def test_save_many_edges(self):
        """Test saving many edges"""

        dynamo.db.save_many_edges(self.edges().values())
        incoming = dynamo.db.get_table('edges_incoming')

        results = list(incoming.batch_get(keys=[{'fbid_source': s, 'fbid_target': t}
                                                for s, t in self.edges().keys()]))

        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              self.edges().keys())

        for x in results:
            d = dict(x.items())
            edge = self.edges().get((x['fbid_source'], x['fbid_target']))
            dynamo.db._remove_null_values(edge)

            # munge the raw dict from dynamo in a compatible way
            assert 'updated' in d
            del d['updated']
            self.assertDictEqual(edge, d)

        outgoing = dynamo.db.get_table('edges_outgoing')

        results = list(outgoing.batch_get(keys=[{'fbid_source': s, 'fbid_target': t}
                                                for s, t in self.edges().keys()]))

        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              self.edges().keys())

    def test_fetch_edge(self):
        """Test fetching a single edge"""
        self.save_edge()

        d = dynamo.db.fetch_edge(100, 200)
        self.assertIsInstance(d, dict)
        assert 'updated' in d
        del d['updated']

        e = self.edges()[(100, 200)]
        dynamo.db._remove_null_values(e)
        self.assertDictEqual(d, e)

    def test_fetch_many_edges(self):
        """Test fetching many edges"""
        dynamo.db.save_many_edges(self.edges().values())

        results = list(dynamo.db.fetch_many_edges(self.edges().keys()))
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              self.edges().keys())

        for x in results:
            d = dict(x.items())
            edge = self.edges().get((x['fbid_source'], x['fbid_target']))
            dynamo.db._remove_null_values(edge)

            # munge the raw dict from dynamo in a compatible way
            assert 'updated' in d
            del d['updated']
            self.assertDictEqual(edge, d)

    def test_fetch_all_incoming_edges(self):
        """Test fetching all edges"""
        dynamo.db.save_many_edges(self.edges().values())

        results = list(dynamo.db.fetch_all_incoming_edges())
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              self.edges().keys())

        for x in results:
            d = dict(x.items())
            edge = self.edges().get((x['fbid_source'], x['fbid_target']))
            dynamo.db._remove_null_values(edge)

            # munge the raw dict from dynamo in a compatible way
            assert 'updated' in d
            del d['updated']
            self.assertDictEqual(edge, d)

    def test_fetch_incoming_edges(self):
        """Test fetching incoming edges"""
        dynamo.db.save_many_edges(self.edges().values())

        results = list(dynamo.db.fetch_incoming_edges(200))
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              [(100, 200), (101, 200)])

        for x in results:
            d = dict(x.items())
            edge = self.edges().get((x['fbid_source'], x['fbid_target']))
            dynamo.db._remove_null_values(edge)

            # munge the raw dict from dynamo in a compatible way
            assert 'updated' in d
            del d['updated']
            self.assertDictEqual(edge, d)

    def test_fetch_outgoing_edges(self):
        """Test fetching outgoing edges"""
        dynamo.db.save_many_edges(self.edges().values())

        results = list(dynamo.db.fetch_outgoing_edges(100))
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              [(100, 200), (100, 202)])

        for x in results:
            d = dict(x.items())
            edge = self.edges().get((x['fbid_source'], x['fbid_target']))
            dynamo.db._remove_null_values(edge)

            # munge the raw dict from dynamo in a compatible way
            assert 'updated' in d
            del d['updated']
            self.assertDictEqual(edge, d)

    def test_fetch_incoming_edges_newer_than(self):
        """Test fetching incoming edges with newer than date"""
        # save everything with "old" date
        with freeze_time('2013-01-01'):
            dynamo.db.save_many_edges(self.edges().values())

        # save edge (100, 200) with a newer date
        with freeze_time('2013-01-06'):
            e = self.edges()[(100, 200)]
            dynamo.db.save_edge(**e)

        results = list(dynamo.db.fetch_incoming_edges(200, newer_than=datetime.datetime(2013, 1, 5, tzinfo=timezone.utc)))

        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              [(100, 200)])

        d = results[0]
        self.assertIsInstance(d, dict)
        assert 'updated' in d
        del d['updated']
        e = self.edges()[(100, 200)]
        dynamo.db._remove_null_values(e)
        self.assertDictEqual(d, e)

        # empty results
        empty = list(dynamo.db.fetch_incoming_edges(200, newer_than=datetime.datetime(2013, 1, 10, tzinfo=timezone.utc)))
        self.assertItemsEqual(empty, [])

    def test_fetch_outgoing_edges_newer_than(self):
        """Test fetching outgoing edges newer than date"""
        # save everything with "old" date
        with freeze_time('2013-01-01'):
            dynamo.db.save_many_edges(self.edges().values())

        # save edge (100, 200) with a newer date
        with freeze_time('2013-01-06'):
            e = self.edges()[(100, 200)]
            dynamo.db.save_edge(**e)

        results = list(dynamo.db.fetch_outgoing_edges(100, newer_than=datetime.datetime(2013, 1, 5, tzinfo=timezone.utc)))

        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              [(100, 200)])

        d = results[0]
        self.assertIsInstance(d, dict)
        assert 'updated' in d
        del d['updated']
        e = self.edges()[(100, 200)]
        dynamo.db._remove_null_values(e)
        self.assertDictEqual(d, e)

        # empty results
        empty = list(dynamo.db.fetch_outgoing_edges(100, newer_than=datetime.datetime(2013, 1, 10, tzinfo=timezone.utc)))
        self.assertItemsEqual(empty, [])
