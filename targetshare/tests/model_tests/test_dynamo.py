import datetime
import os.path
import types

from django.utils import timezone
from freezegun import freeze_time
from nose import tools

from targetshare.models import datastructs, dynamo

from .. import EdgeFlipTestCase, DATA_PATH


def _remove_null_values(dict_):
    """Modify a dict in place by deleting items having null-ish values. For internal use."""
    considered_types = (basestring, set, tuple, list, dict, types.NoneType)
    for key, value in dict_.items():
        if isinstance(value, considered_types) and not value:
            del dict_[key]


def test_remove_null_values():
    '''test internal _remove_null_values'''
    good = {"string": 'wat',
            "num": 9000,
            "zero": 0,
            "set": {1, 2, 3},
            "dict": {'foo': 42}}
    good_ = good.copy()
    _remove_null_values(good_)
    tools.eq_(good_, good)

    bad = {"string": '',
           "set": set(),
           "dict": {}}
    bad_ = bad.copy()
    _remove_null_values(bad_)
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
        item = dynamo.User(
            fbid=1234,
            fname='Alice',
            lname='Apples',
            email='alice@example.com',
            gender='Female',
            birthday=datetime.datetime(1950, 1, 1, tzinfo=timezone.utc),
        )
        item.save()
        return item

    def save_users(self):
        with dynamo.User.items.batch_write() as batch:
            for user in self.users().values():
                batch.put_item(user)

    def test_save_user_new(self):
        """Test saving a new user"""
        self.save_alice()
        x = dynamo.User.items.get_item(fbid=1234)
        self.assertEqual(x.fname, 'Alice')
        self.assertEqual(x.fbid, 1234)
        self.assertEqual(x.birthday, datetime.datetime(1950, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(x.updated, datetime.datetime(2013, 1, 1, tzinfo=timezone.utc))
        self.assertIsNone(x.city)
        self.assertIsNone(x.state)

    def test_save_user_update(self):
        """Test updating an existing user"""
        alice = self.save_alice()

        # update alice
        alice.city = 'Anchorage'
        alice.state = 'Alaska'
        alice.partial_save()

        alice1 = dynamo.User.items.get_item(fbid=1234)
        self.assertEqual(alice1['fname'], 'Alice')
        self.assertEqual(alice1['fbid'], 1234)
        self.assertEqual(alice1['city'], 'Anchorage')
        self.assertEqual(alice1['state'], 'Alaska')

    def test_save_quotes(self):
        quotes = open(os.path.join(DATA_PATH, 'longquote.txt')).read()
        item = dynamo.User(
            fbid=1234,
            fname='Alice',
            lname='Apples',
            email='alice@example.com',
            gender='Female',
            birthday=datetime.datetime(1950, 1, 1, tzinfo=timezone.utc),
            quotes=quotes,
        )
        self.assertEqual(len(item.quotes), 5)
        self.assertIn('Berapa kali ku harus katakan cinta', item.quotes)

    def test_save_quotes_dos(self):
        quotes = open(os.path.join(DATA_PATH, 'longquote.txt')).read()
        item = dynamo.User(
            fbid=1234,
            fname='Alice',
            lname='Apples',
            email='alice@example.com',
            gender='Female',
            birthday=datetime.datetime(1950, 1, 1, tzinfo=timezone.utc),
            quotes=quotes.replace('\n', '\r\n'),
        )
        self.assertEqual(len(item.quotes), 5)
        self.assertIn('Berapa kali ku harus katakan cinta', item.quotes)

    def test_save_quotes_long(self):
        quotes = '\n\n'.join('{}. All work and no play...'.format(count)
                             for count in xrange(1, 151))
        item = dynamo.User(
            fbid=1234,
            fname='Alice',
            lname='Apples',
            email='alice@example.com',
            gender='Female',
            birthday=datetime.datetime(1950, 1, 1, tzinfo=timezone.utc),
            quotes=quotes,
        )
        self.assertEqual(len(quotes.split('\n\n')), 150)
        self.assertEqual(len(item.quotes), 100)
        self.assertIn('100. All work and no play...', item.quotes)

    def test_fetch_user(self):
        """Test fetching an existing user"""
        self.save_alice()
        alice1 = dynamo.User.items.get_item(fbid=1234)
        self.assertEqual(alice1['fbid'], 1234)
        self.assertEqual(alice1['birthday'], datetime.datetime(1950, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(alice1['email'], 'alice@example.com')
        self.assertEqual(alice1['gender'], 'Female')
        self.assertNotIn('city', alice1)
        self.assertNotIn('state', alice1)

    def test_save_many_users(self):
        self.save_users()

        users = self.users()
        keys = [{'fbid': key} for key in users]
        results = dynamo.User.items.batch_get(keys=keys)
        self.assertGreater(len(results), 0)
        self.assertItemsEqual((item['fbid'] for item in results), users)
        for item in results:
            data = dict(item)
            user = self.users()[item['fbid']]

            # Munge data to be comparable:
            _remove_null_values(user)
            data['fbid'] = int(data['fbid'])
            data.pop('updated')

            self.assertDictEqual(data, user)

    def test_fetch_many_users(self):
        """Test fetching many users"""
        self.save_users()
        users = self.users()
        for user in dynamo.User.items.batch_get([{'fbid': fbid} for fbid in self.users()]):
            self.assertIn('updated', user)
            del user['updated']

            data = dict(
                (key, value) for key, value in users[user.fbid].items()
                if value or not isinstance(value, (types.NoneType, basestring, set, list, tuple))
            )
            self.assertDictEqual(dict(user), data)


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
        x = dynamo.Token.items.get_item(fbid=1234, appid=666)
        self.assertEqual(x['fbid'], 1234)
        self.assertEqual(x['appid'], 666)
        self.assertEqual(x['token'], 'DECAFBAD')
        self.assertEqual(x['expires'], self.expiry)
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

        token = dynamo.Token.items.get_item(fbid=1234, appid=666)
        self.assertIn('updated', token)
        del token['updated']

        self.assertEqual(token['fbid'], 1234)
        self.assertEqual(token['appid'], 666)
        self.assertEqual(token['token'], 'DECAFBAD')
        self.assertEqual(token['expires'], self.expiry)

    def test_fetch_many_tokens(self):
        """Test fetching many tokens"""
        tokens = self.tokens()
        for data in tokens.values():
            dynamo.Token.items.put_item(data)

        for token in dynamo.Token.items.batch_get([{'fbid': fbid, 'appid': appid}
                                                   for fbid, appid in tokens]):
            data = tokens[(token['fbid'], token['appid'])]
            token = dict(token)
            del token['updated']
            self.assertDictEqual(token, data)


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

    @staticmethod
    def save_edges(edges):
        datastructs.UserNetwork(datastructs.Edge(None, None, edge) for edge in edges).write()

    def save_edge(self):
        """helper to save a single edge, (100, 200)"""
        self.save_edges([self.edges()[(100, 200)]])

    def test_save_edge(self):
        """Test saving a new edge"""
        self.save_edge()
        x = dynamo.IncomingEdge.items.get_item(fbid_source=100, fbid_target=200)
        assert 'updated' in x
        del x['updated']
        d = dict(x.items())

        e = self.edges()[(100, 200)]
        _remove_null_values(e)
        self.assertDictEqual(d, e)

        x = dynamo.OutgoingEdge.items.get_item(fbid_source=100, fbid_target=200)
        assert 'updated' in x
        del x['updated']
        d = dict(x.items())
        self.assertDictEqual(d, dict(fbid_source=100, fbid_target=200))

    def test_save_many_edges(self):
        """Test saving many edges"""
        edges = self.edges()
        self.save_edges(edges.values())

        results = dynamo.IncomingEdge.items.batch_get(keys=[
            {'fbid_source': s, 'fbid_target': t}
            for s, t in edges
        ])
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              edges.keys())

        for x in results:
            d = dict(x.items())
            del d['updated']
            edge = edges.get((x['fbid_source'], x['fbid_target']))
            _remove_null_values(edge)
            self.assertDictEqual(edge, d)

        results = dynamo.OutgoingEdge.items.batch_get(keys=[
            {'fbid_source': s, 'fbid_target': t}
            for s, t in edges
        ])
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              edges.keys())

    def test_fetch_edge(self):
        """Test fetching a single edge"""
        self.save_edge()

        edge = dynamo.IncomingEdge.items.get_item(fbid_source=100, fbid_target=200)
        self.assertIn('updated', edge)
        del edge['updated']

        data = self.edges()[(100, 200)]
        _remove_null_values(data)
        self.assertDictEqual(dict(edge), data)

    def test_fetch_many_edges(self):
        """Test fetching many edges"""
        edge_data = self.edges()
        self.save_edges(edge_data.values())
        edges_incoming = dynamo.IncomingEdge.items.batch_get([
            {'fbid_source': fbid_source, 'fbid_target': fbid_target}
            for fbid_source, fbid_target in edge_data.keys()
        ])
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in edges_incoming],
                              edge_data.keys())

        for x in edges_incoming:
            d = dict(x)
            del d['updated']
            edge = edge_data.get((x['fbid_source'], x['fbid_target']))
            _remove_null_values(edge)
            self.assertDictEqual(edge, d)

    def test_fetch_all_incoming_edges(self):
        """Test fetching all edges"""
        self.save_edges(self.edges().values())

        results = dynamo.IncomingEdge.items.scan()
        self.assertGreater(len(results), 0)
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              self.edges().keys())
        for x in results:
            d = dict(x.items())
            edge = self.edges().get((x['fbid_source'], x['fbid_target']))
            _remove_null_values(edge)

            # munge the raw dict from dynamo in a compatible way
            assert 'updated' in d
            del d['updated']
            self.assertDictEqual(edge, d)

    def test_fetch_incoming_edges(self):
        """Test fetching incoming edges"""
        self.save_edges(self.edges().values())

        results = dynamo.IncomingEdge.items.query(fbid_target__eq=200)
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              [(100, 200), (101, 200)])
        for x in results:
            d = dict(x.items())
            edge = self.edges().get((x['fbid_source'], x['fbid_target']))
            _remove_null_values(edge)

            # munge the raw dict from dynamo in a compatible way
            assert 'updated' in d
            del d['updated']
            self.assertDictEqual(edge, d)

    def test_fetch_outgoing_edges(self):
        """Test fetching outgoing edges"""
        self.save_edges(self.edges().values())

        results = dynamo.OutgoingEdge.incoming_edges.query(fbid_source__eq=100)
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              [(100, 200), (100, 202)])
        for x in results:
            d = dict(x.items())
            edge = self.edges().get((x['fbid_source'], x['fbid_target']))
            _remove_null_values(edge)

            # munge the raw dict from dynamo in a compatible way
            assert 'updated' in d
            del d['updated']
            self.assertDictEqual(edge, d)

    def test_fetch_incoming_edges_newer_than(self):
        """Test fetching incoming edges with newer than date"""
        # save everything with "old" date
        with freeze_time('2013-01-01'):
            self.save_edges(self.edges().values())

        # save edge (100, 200) with a newer date
        with freeze_time('2013-01-06'):
            e = self.edges()[(100, 200)]
            self.save_edges([e])

        results = dynamo.IncomingEdge.items.query(
            fbid_target__eq=200,
            index='updated',
            updated__gt=datetime.datetime(2013, 1, 5, tzinfo=timezone.utc),
        )
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              [(100, 200)])

        d = results[0]
        assert 'updated' in d
        del d['updated']
        e = self.edges()[(100, 200)]
        _remove_null_values(e)
        self.assertDictEqual(dict(d), e)

        # empty results
        empty = dynamo.IncomingEdge.items.query(
            fbid_target__eq=200,
            index='updated',
            updated__gt=datetime.datetime(2013, 1, 10, tzinfo=timezone.utc),
        )
        self.assertSequenceEqual(empty, ())

    def test_fetch_outgoing_edges_newer_than(self):
        """Test fetching outgoing edges newer than date"""
        # save everything with "old" date
        with freeze_time('2013-01-01'):
            self.save_edges(self.edges().values())

        # save edge (100, 200) with a newer date
        with freeze_time('2013-01-06'):
            e = self.edges()[(100, 200)]
            self.save_edges([e])

        results = dynamo.OutgoingEdge.incoming_edges.query(
            fbid_source__eq=100,
            index='updated',
            updated__gt=datetime.datetime(2013, 1, 5, tzinfo=timezone.utc),
        )
        self.assertItemsEqual([(x['fbid_source'], x['fbid_target']) for x in results],
                              [(100, 200)])

        d = results[0]
        assert 'updated' in d
        del d['updated']
        e = self.edges()[(100, 200)]
        _remove_null_values(e)
        self.assertDictEqual(dict(d), e)

        # empty results
        empty = dynamo.OutgoingEdge.incoming_edges.query(
            fbid_source__eq=100,
            index='updated',
            updated__gt=datetime.datetime(2013, 1, 10, tzinfo=timezone.utc),
        )
        self.assertSequenceEqual(empty, [])
