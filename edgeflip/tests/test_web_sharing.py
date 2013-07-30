import json
from datetime import date

from mock import patch, Mock

from edgeflip.tests import EdgeFlipTestCase
from edgeflip import (
    client_db_tools as cdb,
    datastructs
)


class TestWebSharing(EdgeFlipTestCase):

    def setUp(self):
        super(TestWebSharing, self).setUp()
        self.params = {
            'fbid': '1',
            'token': 1,
            'num': 9,
            'sessionid': 'fake-session',
            'campaignid': 1,
            'contentid': 1,
            'mockmode': True,
        }
        self.test_user = datastructs.UserInfo(
            uid=1,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            sex='male',
            birthday=date(1984, 1, 1),
            city='Chicago',
            state='Illinois',
        )
        self.test_edge = datastructs.Edge(
            self.test_user,
            self.test_user,
            None
        )
        self.test_filter = cdb.ChoiceSetFilter(
            1,
            2,
            'all',
            features=[
                (
                    'state',
                    'in',
                    ['Illinois', 'California', 'Massachusetts', 'New York']
                )
            ]
        )
        self.test_cs = cdb.ChoiceSet(1, [self.test_filter])

    def _make_request(self, url='/faces', status_code=200, params=None):
        ''' Helper function for making HTTP requests to our various urls '''
        params = params if params else self.params
        headers = [
            ('Content-Type', 'application/json; charset=utf-8'),
            ('X-Requested-With', 'XMLHttpRequest'),
        ]
        response = self.app.post(
            url,
            headers=headers,
            content_type='application/json',
            base_url='http://local/',
            data=json.dumps(params)
        )
        self.assertStatusCode(response, status_code)
        return response

    def test_faces_get(self):
        ''' Faces endpoint requires POST, so we expect a 405 here '''
        response = self.app.get('/faces')
        self.assertStatusCode(response, 405)

    def test_faces_initial_entry(self):
        ''' Tests a users first request to the Faces endpoint. We expect to
        receive a JSON response with a status of waiting along with the
        tasks IDs of the Celery jobs we started
        '''
        response = self._make_request()
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'waiting')
        assert data['px3_task_id']
        assert data['px4_task_id']

    @patch('edgeflip.web.sharing.celery')
    def test_faces_px3_wait(self, celery_mock):
        ''' Tests that we receive a JSON status of "waiting" when our px3
        task isn't yet complete
        '''
        result_mock = Mock()
        result_mock.ready.return_value = False
        async_mock = Mock()
        async_mock.side_effect = [
            result_mock,
            result_mock
        ]
        celery_mock.celery.AsyncResult = async_mock
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid'
        })
        response = self._make_request()
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'waiting')

    @patch('edgeflip.web.sharing.celery')
    def test_faces_px4_wait(self, celery_mock):
        ''' Test that even if px3 is done, we'll wait on px4 if we're not
        ready to give up on it yet
        '''
        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = True
        px4_result_mock = Mock()
        px4_result_mock.ready.return_value = False
        async_mock = Mock()
        async_mock.side_effect = [
            px3_result_mock,
            px4_result_mock
        ]
        celery_mock.celery.AsyncResult = async_mock
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid'
        })
        response = self._make_request()
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'waiting')

    @patch('edgeflip.web.sharing.celery')
    def test_faces_last_call(self, celery_mock):
        ''' Test that gives up on waiting for the px4 result, and serves the
        px3 results
        '''
        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = True
        px3_result_mock.result = (
            [self.test_edge],
            cdb.TieredEdges(edges=[self.test_edge], campaignId=1, contentId=1),
            self.test_filter.filterId,
            self.test_filter.urlSlug,
            1,
            1
        )
        px4_result_mock = Mock()
        px4_result_mock.ready.return_value = False
        px4_result_mock.successful.return_value = False
        async_mock = Mock()
        async_mock.side_effect = [
            px3_result_mock,
            px4_result_mock
        ]
        celery_mock.celery.AsyncResult = async_mock
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid',
            'last_call': True,
        })
        response = self._make_request()
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        assert data['html']

    @patch('edgeflip.web.sharing.celery')
    def test_faces_complete_crawl(self, celery_mock):
        ''' Test that completes both px3 and px4 crawls '''
        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = True
        px3_result_mock.result = (
            [self.test_edge],
            cdb.TieredEdges(edges=[self.test_edge], campaignId=1, contentId=1),
            self.test_filter.filterId,
            self.test_filter.urlSlug,
            1,
            1
        )
        px4_result_mock = Mock()
        px4_result_mock.ready.return_value = True
        px4_result_mock.successful.return_value = True
        px4_result_mock.result = [self.test_edge]
        async_mock = Mock()
        async_mock.side_effect = [
            px3_result_mock,
            px4_result_mock
        ]
        celery_mock.celery.AsyncResult = async_mock
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid',
            'last_call': True,
        })
        response = self._make_request()
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        assert data['html']
