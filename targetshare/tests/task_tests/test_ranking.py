import itertools
import types

import celery
from django.utils import timezone
from freezegun import freeze_time
from mock import patch

from targetshare import models
from targetshare.tasks import ranking
from targetshare.integration.facebook.client import urllib2

from .. import EdgeFlipTestCase, patch_facebook


class RankingTestCase(EdgeFlipTestCase):

    def setUp(self):
        super(RankingTestCase, self).setUp()
        expires = timezone.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.token = models.dynamo.Token(fbid=1, appid=1, token='1', expires=expires)


class TestProximityRankThree(RankingTestCase):

    @patch_facebook
    def test_proximity_rank_three(self):
        ''' Test that calls tasks.proximity_rank_three with dummy args. This
        method is simply supposed to create a celery Task chain, and return the
        ID to the caller. As such, we assert that we receive a valid Celery
        task ID.
        '''
        task_id = ranking.proximity_rank_three(self.token)
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
        ranked_edges = ranking.px3_crawl(self.token)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)


@freeze_time('2013-01-01')
class TestFiltering(RankingTestCase):

    fixtures = ['test_data']

    @patch_facebook
    def test_perform_filtering(self):
        ''' Runs the filtering celery task '''
        visitor = models.relational.Visitor.objects.create()
        visit = visitor.visits.create(session_id='123', app_id=123, ip='127.0.0.1')
        # FIXME: Because the px3 mock crawl yields random results, this may in
        #        some cases return a set of edges in which none meet the filter
        #        used in this test. That would cause this test to 'fail' even
        #        though all the code is working properly.
        ranked_edges = ranking.px3_crawl(self.token)
        (
            edges_ranked,
            edges_filtered,
            filter_id,
            cs_slug,
            campaign_id,
            content_id,
        ) = ranking.perform_filtering(
            ranked_edges,
            campaign_id=1,
            content_id=1,
            fbid=1,
            visit_id=visit.pk,
            num_faces=10,
        )
        self.assertTrue(edges_ranked)
        self.assertEqual({type(edge) for edge in edges_ranked},
                         {models.datastructs.Edge})
        self.assertIsInstance(edges_filtered, models.datastructs.TieredEdges)
        self.assertEqual({type(edge) for edge in edges_filtered.edges},
                         {models.datastructs.Edge})
        self.assertIsInstance(filter_id, long)
        self.assertIsInstance(cs_slug, (types.NoneType, basestring))

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
        test_edge1 = models.datastructs.UserNetwork.Edge(test_user1, test_user1, None, score=0.5)
        test_edge2 = models.datastructs.UserNetwork.Edge(test_user1, test_user2, None, score=0.4)
        visitor = models.relational.Visitor.objects.create(fbid=1)
        visit = visitor.visits.create(session_id='123', app_id=123, ip='127.0.0.1')

        ranked_edges = [test_edge2, test_edge1]
        edges_ranked, edges_filtered, filter_id, cs_slug, campaign_id, content_id = ranking.perform_filtering(
            ranked_edges,
            campaign_id=5,
            content_id=1,
            fbid=1,
            visit_id=visit.pk,
            num_faces=10,
        )

        self.assertEquals(edges_filtered.secondary_ids, (1, 2))
        self.assertEquals(edges_filtered[0]['campaign_id'], 5)
        self.assertEquals(edges_filtered[1]['campaign_id'], 4)


class TestProximityRankFour(RankingTestCase):

    @patch_facebook(min_friends=150, max_friends=200)
    @patch('targetshare.tasks.ranking.LOG')
    def test_proximity_rank_four_from_fb(self, logger_mock):
        self.assertFalse(models.dynamo.IncomingEdge.items.scan(limit=1))

        (ranked_edges, hit_fb) = ranking.px4_crawl(self.token)
        self.assertIsInstance(ranked_edges, models.datastructs.UserNetwork)

        post_topics = ranked_edges.post_topics
        self.assertTrue(post_topics)
        assert all(isinstance(pt, models.PostTopics) for pt in post_topics.itervalues())

        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)

        interactions = tuple(itertools.chain.from_iterable(x.interactions
                                                           for x in ranked_edges))
        self.assertTrue(interactions)
        assert all(isinstance(i, models.PostInteractions) for i in interactions)

        assert all(x.incoming.post_likes is not None for x in ranked_edges)
        self.assertTrue(models.dynamo.IncomingEdge.items.scan(limit=1))

        self.assertIn('falling back to FB', logger_mock.info.call_args[0][0])
        # We know we have a call to get the user and the friend count at the
        # very least. However, hitting FB should spawn many more hits to FB
        self.assertGreater(urllib2.urlopen.call_count, 2)

    @patch_facebook(min_friends=1, max_friends=99)
    @patch('targetshare.tasks.ranking.LOG')
    def test_proximity_rank_four_less_than_100_friends(self, logger_mock):
        self.assertFalse(models.dynamo.IncomingEdge.items.scan(limit=1))

        (ranked_edges, hit_fb) = ranking.px4_crawl(self.token)
        self.assertIsInstance(ranked_edges, models.datastructs.UserNetwork)
        assert all(isinstance(x, models.datastructs.Edge) for x in ranked_edges)
        assert all(x.incoming.post_likes is not None for x in ranked_edges)

        self.assertTrue(models.dynamo.IncomingEdge.items.scan(limit=1))
        self.assertIn(
            'Has %r friends, hitting FB',
            logger_mock.info.call_args[0][0]
        )
        # We know we have a call to get the user and the friend count at the
        # very least. However, hitting FB should spawn many more hits to FB
        self.assertGreater(urllib2.urlopen.call_count, 2)

    @patch_facebook(min_friends=100, max_friends=100)
    @patch('targetshare.tasks.ranking.LOG')
    def test_proximity_rank_four_uses_dynamo(self, logger_mock):
        self.assertFalse(models.dynamo.IncomingEdge.items.scan(limit=1))
        for x in range(0, 100):
            edge = models.IncomingEdge(fbid_source=x, fbid_target=1, post_likes=x)
            edge.save()
            user = models.User(fbid=x)
            user.save()

        (ranked_edges, hit_fb) = ranking.px4_crawl(self.token)
        self.assertIsInstance(ranked_edges, models.datastructs.UserNetwork)
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
