from targetshare.tests import EdgeFlipTestCase
from targetshare import (
    client_db_tools as cdb,
    datastructs,
    tasks
)
from targetshare.celery import celery
import datetime


class TestCeleryTasks(EdgeFlipTestCase):

    def setUp(self):
        super(TestCeleryTasks, self).setUp()
        expires = datetime.datetime(2100, 1, 1, 12, 0, 0)
        self.token = datastructs.TokenInfo('1', '1', '1', expires)

    def test_proximity_rank_three(self):
        ''' Test that calls tasks.proximity_rank_three with dummy args. This
        method is simply supposed to create a celery Task chain, and return the
        ID to the caller. As such, we assert that we receive a valid Celery
        task ID.
        '''
        task_id = tasks.proximity_rank_three(True, 1, self.token)
        assert task_id
        assert celery.AsyncResult(task_id)

    def test_px3_crawl(self):
        ''' Run the px3_crawl celery task without throwing it
        through the celery/rabbitmq stack, because we're testing our code,
        not celerys.

        Pass in True for mock mode, a dummy FB id, and a dummy token. Should
        get back a lengthy list of Edges.
        '''
        ranked_edges = tasks.px3_crawl(True, 1, self.token)
        assert all((isinstance(x, datastructs.Edge) for x in ranked_edges))

    def test_perform_filtering(self):
        ''' Runs the filtering celery task '''
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
        assert all((isinstance(x, datastructs.Edge) for x in edges_ranked))
        assert isinstance(edges_filtered, cdb.TieredEdges)
        assert all((isinstance(x, datastructs.Edge) for x in edges_filtered.edges()))
        assert isinstance(filter_id, int)
        assert (cs_slug is None) or (isinstance(cs_slug, basestring))

    def test_proximity_rank_four(self):
        ranked_edges = tasks.proximity_rank_four(True, 1, self.token)
        assert all((isinstance(x, datastructs.Edge) for x in ranked_edges))
        assert all((x.countsIn.postLikes is not None for x in ranked_edges))

        # Make sure some edges were created.
        curs = self.conn.cursor()
        sql = 'SELECT * FROM edges WHERE fbid_target=%s'
        row_count = curs.execute(sql, 1)
        assert row_count

    def test_fallback_cascade(self):
        # Some test users and edges
        test_user1 = datastructs.UserInfo(
            uid=1,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            sex='male',
            birthday=datetime.date(1984, 1, 1),
            city='Chicago',
            state='Illinois'
        )
        test_user2 = datastructs.UserInfo(
            uid=2,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            sex='male',
            birthday=datetime.date(1984, 1, 1),
            city='Toledo',
            state='Ohio'
        )
        test_edge1 = datastructs.Edge(
            test_user1,
            test_user1,
            None
        )
        test_edge1.score = 0.5
        test_edge2 = datastructs.Edge(
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

        self.assertEquals(edges_filtered.secondaryIds(), [1, 2])
        self.assertEquals(edges_filtered.tiers[0]['campaignId'], 5)
        self.assertEquals(edges_filtered.tiers[1]['campaignId'], 4)
