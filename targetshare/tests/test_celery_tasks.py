import celery

from django.utils import timezone
from freezegun import freeze_time
from mock import patch

from targetshare import models
from targetshare.tasks import db, ranking
from targetshare.integration.facebook.client import urllib2

from . import EdgeFlipTestCase, patch_facebook


@freeze_time('2013-01-01')
class TestRankingTasks(EdgeFlipTestCase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestRankingTasks, self).setUp()
        expires = timezone.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.token = models.dynamo.Token(fbid=1, appid=1, token='1', expires=expires)

    @patch_facebook
    def test_proximity_rank_three(self):
        ''' Test that calls tasks.proximity_rank_three with dummy args. This
        method is simply supposed to create a celery Task chain, and return the
        ID to the caller. As such, we assert that we receive a valid Celery
        task ID.
        '''
        task_id = ranking.proximity_rank_three(False, 1, self.token)
        assert task_id
        assert celery.current_app.AsyncResult(task_id)

    @patch_facebook
    def test_px3_crawl(self):
        ''' Run the px3_crawl celery task without throwing it
        through the celery/rabbitmq stack, because we're testing our code,
        not celerys.

        Pass in True for mock mode, a dummy FB id, and a dummy token. Should
        get back a lengthy list of Edges.
        '''
        ranked_edges = ranking.px3_crawl(False, 1, self.token)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)

    @patch_facebook
    def test_perform_filtering(self):
        ''' Runs the filtering celery task '''
        visitor = models.relational.Visitor.objects.create()
        visit = visitor.visits.create(session_id='123', app_id=123, ip='127.0.0.1')
        # FIXME: Because the px3 mock crawl yields random results, this may in
        #        some cases return a set of edges in which none meet the filter
        #        used in this test. That would cause this test to 'fail' even
        #        though all the code is working properly.
        ranked_edges = ranking.px3_crawl(False, 1, self.token)
        edges_ranked, edges_filtered, filter_id, cs_slug, campaign_id, content_id = ranking.perform_filtering(
            ranked_edges,
            campaignId=1,
            contentId=1,
            fbid=1,
            visit_id=visit.pk,
            numFace=10,
        )
        assert all(isinstance(x, models.datastructs.Edge) for x in edges_ranked)
        assert isinstance(edges_filtered, models.datastructs.TieredEdges)
        assert all(isinstance(x, models.datastructs.Edge) for x in edges_filtered.edges)
        assert isinstance(filter_id, long)
        assert cs_slug is None or isinstance(cs_slug, basestring)

    @patch_facebook(min_friends=150, max_friends=200)
    @patch('targetshare.tasks.ranking.logger')
    def test_proximity_rank_four_from_fb(self, logger_mock):
        self.assertFalse(models.dynamo.IncomingEdge.items.scan(limit=1))

        ranked_edges = ranking.proximity_rank_four(False, 1, self.token)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)
        assert all(x.incoming.post_likes is not None for x in ranked_edges)

        self.assertTrue(models.dynamo.IncomingEdge.items.scan(limit=1))
        self.assertIn('Falling back to FB', logger_mock.info.call_args[0][0])
        # We know we have a call to get the user and the friend count at the
        # very least. However, hitting FB should spawn many more hits to FB
        self.assertTrue(urllib2.urlopen.call_count > 2)

    @patch_facebook(min_friends=1, max_friends=99)
    @patch('targetshare.tasks.ranking.logger')
    def test_proximity_rank_four_less_than_100_friends(self, logger_mock):
        self.assertFalse(models.dynamo.IncomingEdge.items.scan(limit=1))

        ranked_edges = ranking.proximity_rank_four(False, 1, self.token)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)
        assert all(x.incoming.post_likes is not None for x in ranked_edges)

        self.assertTrue(models.dynamo.IncomingEdge.items.scan(limit=1))
        self.assertIn(
            'Has less than 100 friends, hitting FB',
            logger_mock.info.call_args[0][0]
        )
        # We know we have a call to get the user and the friend count at the
        # very least. However, hitting FB should spawn many more hits to FB
        self.assertTrue(urllib2.urlopen.call_count > 2)

    @patch_facebook(min_friends=100, max_friends=100)
    @patch('targetshare.tasks.ranking.logger')
    def test_proximity_rank_four_uses_dynamo(self, logger_mock):
        self.assertFalse(models.dynamo.IncomingEdge.items.scan(limit=1))
        for x in range(0, 100):
            edge = models.IncomingEdge(fbid_source=x, fbid_target=1, post_likes=x)
            edge.save()
            user = models.User(fbid=x)
            user.save()

        ranked_edges = ranking.proximity_rank_four(False, 1, self.token)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)
        assert all(x.incoming.post_likes is not None for x in ranked_edges)

        self.assertTrue(models.dynamo.IncomingEdge.items.scan(limit=1))
        self.assertIn(
            'using Dynamo data.',
            logger_mock.info.call_args[0][0]
        )
        # One call to get the user, the other to get the friend count
        self.assertEqual(
            urllib2.urlopen.call_count,
            2
        )

    def test_fallback_cascade(self):
        # Some test users and edges
        test_user1 = models.User(
            fbid=1,
            fname='Test',
            lname='User',
            email='test@example.com',
            gender='male',
            birthday=timezone.datetime(1984, 1, 1, tzinfo=timezone.utc),
            city='Chicago',
            state='Illinois'
        )
        test_user2 = models.User(
            fbid=2,
            fname='Test',
            lname='User',
            email='test@example.com',
            gender='male',
            birthday=timezone.datetime(1984, 1, 1, tzinfo=timezone.utc),
            city='Toledo',
            state='Ohio'
        )
        test_edge1 = models.datastructs.Edge(test_user1, test_user1, None, score=0.5)
        test_edge2 = models.datastructs.Edge(test_user1, test_user2, None, score=0.4)
        visitor = models.relational.Visitor.objects.create(fbid=1)
        visit = visitor.visits.create(session_id='123', app_id=123, ip='127.0.0.1')

        ranked_edges = [test_edge2, test_edge1]
        edges_ranked, edges_filtered, filter_id, cs_slug, campaign_id, content_id = ranking.perform_filtering(
            ranked_edges,
            campaignId=5,
            contentId=1,
            fbid=1,
            visit_id=visit.pk,
            numFace=10,
        )

        self.assertEquals(edges_filtered.secondary_ids, (1, 2))
        self.assertEquals(edges_filtered[0]['campaignId'], 5)
        self.assertEquals(edges_filtered[1]['campaignId'], 4)


class TestDatabaseTasks(EdgeFlipTestCase):

    def test_delayed_bulk_create(self):
        """Task bulk_create calls objects.bulk_create with objects passed"""
        clients = [
            models.relational.Client(
                name="Client {}".format(count),
                codename='client-{}'.format(count)
            )
            for count in xrange(1, 11)
        ]
        client_count = models.relational.Client.objects.count()
        db.bulk_create(clients)
        self.assertEqual(models.relational.Client.objects.count(), client_count + 10)

    def test_delayed_obj_save(self):
        """Task delayed_save calls the save method of the object passed"""
        client = models.relational.Client(name="testy")
        matching_clients = models.relational.Client.objects.filter(name="testy")
        assert not matching_clients.exists()
        db.delayed_save(client)
        assert matching_clients.exists()

    def test_delayed_item_save(self):
        user = models.dynamo.User(fbid=1234)
        self.assertFalse(models.dynamo.User.items.batch_get(keys=[user.get_keys()]))
        db.delayed_save(user)
        self.assertTrue(models.dynamo.User.items.batch_get(keys=[user.get_keys()]))

    def test_delayed_item_save_conflict(self):
        """Dynamo race conditions are caught and data merged"""
        # Provision item:
        alice = models.dynamo.User({
            'fbid': 1234,
            'fname': 'Alice',
            'lname': 'Apples',
            'email': 'aliceapples@yahoo.com',
            'gender': 'Female',
        })
        alice.save()

        # Make changes:
        alice['lname'] = 'Applesauce'
        alice['email'] = 'aliceapplesauce@yahoo.com'

        # Make those changes stale:
        alice_fresh = models.dynamo.User.items.get_item(**alice.get_keys())
        alice_fresh['fname'] = 'Ally'
        alice_fresh['email'] = 'allyapples@yahoo.com'
        alice_fresh.partial_save()

        # Attempt to save stale changes:
        db.partial_save(alice)
        alice_final = models.dynamo.User.items.get_item(**alice.get_keys())
        # Winner of race condition trumps loser:
        self.assertEqual(alice_final['fname'], 'Ally')
        self.assertEqual(alice_final['email'], 'allyapples@yahoo.com')
        # But loser's novel changes make it through:
        self.assertEqual(alice_final['lname'], 'Applesauce')

    def test_delayed_bulk_item_upsert(self):
        # Provision item:
        alice = models.dynamo.User({
            'fbid': 1234,
            'fname': 'Alice',
            'lname': 'Apples',
            'email': 'aliceapples@yahoo.com',
            'gender': 'Female',
            'birthday': timezone.datetime(1945, 4, 14, tzinfo=timezone.utc),
        })
        alice.save()

        # Modify existing item:
        alice['email'] = ''
        alice['fname'] = "Ally"

        # Start new item:
        evan = models.dynamo.User({
            'fbid': 2000,
            'fname': 'Evan',
            'lname': 'Escarole',
            'email': 'evanescarole@hotmail.com',
            'gender': 'Male',
            'birthday': None,
        })

        # Upsert:
        db.upsert([evan, alice])

        alice = models.dynamo.User.items.get_item(**alice.get_keys())
        evan = models.dynamo.User.items.get_item(**evan.get_keys())

        data_a = dict(alice)
        data_a.pop('updated')
        self.assertEqual(data_a, {
            'fbid': 1234,
            'fname': 'Ally', # fname updated
            'lname': 'Apples',
            'email': 'aliceapples@yahoo.com', # Email update ignored (null-y)
            'gender': 'Female',
            'birthday': timezone.datetime(1945, 4, 14, tzinfo=timezone.utc),
        })

        data_e = dict(evan)
        data_e.pop('updated')
        self.assertEqual(data_e, {
            'fbid': 2000,
            'fname': 'Evan',
            'lname': 'Escarole',
            'email': 'evanescarole@hotmail.com',
            'gender': 'Male',
            # birthday ignored
        })
