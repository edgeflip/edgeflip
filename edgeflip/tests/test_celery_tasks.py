from edgeflip.tests import EdgeFlipTestCase
from edgeflip import (
    datastructs,
    tasks
)


class TestCeleryTasks(EdgeFlipTestCase):

    def test_retrive_fb_user_info(self):
        ''' Run the retrieve_fb_user_info celery task without throwing it
        through the celery/rabbitmq stack, because we're testing our code,
        not celerys.

        Pass in True for mock mode, a dummy FB id, and a dummy token. Should
        get back a lengthy list of Edges.
        '''
        token = datastructs.TokenInfo('1', '1', '1', '1')
        user, ranked_edges = tasks.retrieve_fb_user_info(True, 1, token)
        assert isinstance(user, datastructs.UserInfo)
        assert all((isinstance(x, datastructs.Edge) for x in ranked_edges))

        # Make sure some edges were created.
        curs = self.conn.cursor()
        sql = 'SELECT * FROM edges WHERE fbid_target=%s'
        row_count = curs.execute(sql, 1)
        assert row_count
