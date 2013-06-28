from mock import Mock

from edgeflip.tests import EdgeFlipTestCase
from edgeflip import (
    client_db_tools as cdb,
    datastructs,
    tasks
)
from edgeflip.celery import celery


class TestCeleryTasks(EdgeFlipTestCase):

    def test_proximity_rank_three(self):
        ''' Test that calls tasks.proximity_rank_three with dummy args. This
        method is simply supposed to create a celery Task chain, and return the
        ID to the caller. As such, we assert that we receive a valid Celery
        task ID.
        '''
        task_id = tasks.proximity_rank_three(None, None, None)
        assert task_id
        assert celery.AsyncResult(task_id)

    def test_px3_crawl(self):
        ''' Run the px3_crawl celery task without throwing it
        through the celery/rabbitmq stack, because we're testing our code,
        not celerys.

        Pass in True for mock mode, a dummy FB id, and a dummy token. Should
        get back a lengthy list of Edges.
        '''
        token = datastructs.TokenInfo('1', '1', '1', '1')
        ranked_edges = tasks.px3_crawl(True, 1, token)
        assert all((isinstance(x, datastructs.Edge) for x in ranked_edges))

        # Make sure some edges were created.
        curs = self.conn.cursor()
        sql = 'SELECT * FROM edges WHERE fbid_target=%s'
        row_count = curs.execute(sql, 1)
        assert row_count

    def test_perform_filtering(self):
        ''' Runs the filtering celery task '''
        token = datastructs.TokenInfo('1', '1', '1', '1')
        ranked_edges = tasks.px3_crawl(True, 1, token)
        edges, cs_filter, cs, generic = tasks.perform_filtering(
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
        assert all((isinstance(x, datastructs.Edge) for x in edges))
        assert isinstance(cs_filter[0], cdb.ChoiceSetFilter)
        assert isinstance(cs, cdb.ChoiceSet)
        self.assertEqual(generic, [1, 'all'])

    def test_proximity_rank_four(self):
        token = datastructs.TokenInfo('1', '1', '1', '1')
        ranked_edges = tasks.proximity_rank_four(True, 1, token)
        assert all((isinstance(x, datastructs.Edge) for x in ranked_edges))
        assert all((x.countsIn.postLikes is not None for x in ranked_edges))

        # Make sure some edges were created.
        curs = self.conn.cursor()
        sql = 'SELECT * FROM edges WHERE fbid_target=%s'
        row_count = curs.execute(sql, 1)
        assert row_count
