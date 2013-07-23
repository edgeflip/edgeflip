from edgeflip.tests import EdgeFlipTestCase
from edgeflip import (
    client_db_tools as cdb,
    datastructs,
    tasks,
    dynamo
)
from edgeflip.celery import celery

import datetime
from freezegun import freeze_time

@freeze_time('2013-01-01')
class TestCeleryTasks(EdgeFlipTestCase):

    def _token(self):
        '''helper to return a token'''
        return datastructs.TokenInfo(tok='1',
                                     own=1,
                                     app=1,
                                     exp=datetime.datetime.now() +
                                     datetime.timedelta(days=365))


    def test_proximity_rank_three(self):
        ''' Test that calls tasks.proximity_rank_three with dummy args. This
        method is simply supposed to create a celery Task chain, and return the
        ID to the caller. As such, we assert that we receive a valid Celery
        task ID.
        '''
        token = self._token()
        task_id = tasks.proximity_rank_three(True, 1, token)
        assert task_id
        assert celery.AsyncResult(task_id)

    def test_px3_crawl(self):
        ''' Run the px3_crawl celery task without throwing it
        through the celery/rabbitmq stack, because we're testing our code,
        not celerys.

        Pass in True for mock mode, a dummy FB id, and a dummy token. Should
        get back a lengthy list of Edges.
        '''
        token = self._token()
        ranked_edges = tasks.px3_crawl(True, 1, token)
        assert all((isinstance(x, datastructs.Edge) for x in ranked_edges))

    def test_perform_filtering(self):
        ''' Runs the filtering celery task '''
        token = self._token()
        ranked_edges = tasks.px3_crawl(True, 1, token)
        edges, cs_filter, cs, generic, campaign_id, content_id = tasks.perform_filtering(
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
        token = self._token()
        ranked_edges = tasks.proximity_rank_four(True, 1, token)
        assert all((isinstance(x, datastructs.Edge) for x in ranked_edges))
        assert all((x.countsIn.postLikes is not None for x in ranked_edges))

        # Make sure some edges were created.
        edges = list(dynamo.fetch_all_incoming_edges())
        assert edges