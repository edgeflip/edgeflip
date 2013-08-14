import celery

from django.utils import timezone
from freezegun import freeze_time

from targetshare import (
    models,
    tasks,
)

from . import EdgeFlipTestCase


@freeze_time('2013-01-01')
class TestCeleryTasks(EdgeFlipTestCase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestCeleryTasks, self).setUp()
        expires = timezone.datetime(2100, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.token = models.datastructs.TokenInfo('1', '1', '1', expires)

    def test_proximity_rank_three(self):
        ''' Test that calls tasks.proximity_rank_three with dummy args. This
        method is simply supposed to create a celery Task chain, and return the
        ID to the caller. As such, we assert that we receive a valid Celery
        task ID.
        '''
        task_id = tasks.proximity_rank_three(True, 1, self.token)
        assert task_id
        assert celery.current_app.AsyncResult(task_id)

    def test_px3_crawl(self):
        ''' Run the px3_crawl celery task without throwing it
        through the celery/rabbitmq stack, because we're testing our code,
        not celerys.

        Pass in True for mock mode, a dummy FB id, and a dummy token. Should
        get back a lengthy list of Edges.
        '''
        ranked_edges = tasks.px3_crawl(True, 1, self.token)
        assert all((isinstance(x, models.datastructs.Edge) for x in ranked_edges))

    def test_perform_filtering(self):
        ''' Runs the filtering celery task '''
        # FIXME: Because the px3 mock crawl yields random results, this may in
        #        some cases return a set of edges in which none meet the filter
        #        used in this test. That would cause this test to 'fail' even
        #        though all the code is working properly.
        ranked_edges = tasks.px3_crawl(True, 1, self.token)
        edges_ranked, edges_filtered, filter_id, cs_slug, campaign_id, content_id = tasks.perform_filtering(
            ranked_edges,
            'local',
            1,
            1,
            'fake-session-id',
            '127.0.0.1',
            1,
            10,
            ('sharing-social-good', '471727162864364')
        )
        assert all((isinstance(x, models.datastructs.Edge) for x in edges_ranked))
        assert isinstance(edges_filtered, models.datastructs.TieredEdges)
        assert all((isinstance(x, models.datastructs.Edge) for x in edges_filtered.edges))
        assert isinstance(filter_id, long)
        assert (cs_slug is None) or (isinstance(cs_slug, basestring))

    def test_proximity_rank_four(self):
        ranked_edges = tasks.proximity_rank_four(True, 1, self.token)
        assert all((isinstance(x, models.datastructs.Edge) for x in ranked_edges))
        assert all((x.countsIn.postLikes is not None for x in ranked_edges))

        # Make sure some edges were created.
        assert list(models.dynamo.fetch_all_incoming_edges())

    def test_fallback_cascade(self):
        # Some test users and edges
        test_user1 = models.datastructs.UserInfo(
            uid=1,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            sex='male',
            birthday=timezone.datetime(1984, 1, 1, tzinfo=timezone.utc),
            city='Chicago',
            state='Illinois'
        )
        test_user2 = models.datastructs.UserInfo(
            uid=2,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            sex='male',
            birthday=timezone.datetime(1984, 1, 1, tzinfo=timezone.utc),
            city='Toledo',
            state='Ohio'
        )
        test_edge1 = models.datastructs.Edge(
            test_user1,
            test_user1,
            None
        )
        test_edge1.score = 0.5
        test_edge2 = models.datastructs.Edge(
            test_user1,
            test_user2,
            None
        )
        test_edge2.score = 0.4

        ranked_edges = [test_edge2, test_edge1]
        edges_ranked, edges_filtered, filter_id, cs_slug, campaign_id, content_id = tasks.perform_filtering(
            ranked_edges,
            'local',
            5,
            1,
            'fake-session-id',
            '127.0.0.1',
            1,
            10,
            ('sharing-social-good', '471727162864364')
        )

        self.assertEquals(edges_filtered.secondary_ids, (1, 2))
        self.assertEquals(edges_filtered[0]['campaignId'], 5)
        self.assertEquals(edges_filtered[1]['campaignId'], 4)

    def test_delayed_bulk_create(self):
        ''' Tests the tasks.bulk_write_objs task '''
        # FIXME: dynamo
        assert not models.User.objects.exists()
        users = []
        for x in range(10):
            users.append(models.User(
                first_name='Test%s' % x,
                last_name='User',
                fbid=x,
            ))
        tasks.bulk_create(users)
        self.assertEqual(models.User.objects.count(), 10)

    def test_delayed_obj_save(self):
        ''' Tests the tasks.save_model_obj task '''
        # FIXME: dynamo
        assert not models.User.objects.exists()
        tasks.delayed_save(models.User(
            first_name='Test',
            last_name='Delayed_User',
            fbid=100
        ))
        assert models.User.objects.filter(last_name='Delayed_User').exists()
