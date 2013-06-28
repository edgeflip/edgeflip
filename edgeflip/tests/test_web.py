import json

from edgeflip.tests import EdgeFlipTestCase


class TestWeb(EdgeFlipTestCase):

    def test_sharing_get(self):
        ''' Faces endpoint requires POST, so we expect a 405 here '''
        response = self.app.get('/faces')
        self.assertStatusCode(response, 405)

    def test_sharing_initial_entry(self):
        ''' Tests a users first request to the Faces endpoint. We expect to
        receive a JSON response with a status of waiting along with the
        tasks IDs of the Celery jobs we started
        '''
        headers = [
            ('Content-Type', 'application/json; charset=utf-8'),
            ('X-Requested-With', 'XMLHttpRequest'),
        ]
        params = {
            'fbid': '1',
            'token': 1,
            'num': 9,
            'sessionid': 'fake-session',
            'campaignid': 1,
            'contentid': 1,
            'mockmode': True,
        }
        response = self.app.post(
            '/faces',
            headers=headers,
            content_type='application/json',
            base_url='http://local/',
            data=json.dumps(params)
        )
        self.assertStatusCode(response, 200)

        data = json.loads(response.data)
        self.assertEqual(data['status'], 'waiting')
        assert data['px3_task_id']
        assert data['px4_task_id']
