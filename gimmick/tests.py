import json

import mock
from django.core.urlresolvers import reverse

from targetshare.tests import EdgeFlipTestCase, patch_facebook, patch_token


class TestMapView(EdgeFlipTestCase):

    def test_get(self):
        response = self.client.get(reverse('gimmick:map'))
        self.assertStatusCode(response, 200)
        self.assertTemplateUsed(response, 'gimmick/map.html')

    def test_post(self):
        response = self.client.post(reverse('gimmick:map'))
        self.assertStatusCode(response, 200)
        self.assertTemplateUsed(response, 'gimmick/map.html')


class TestDataView(EdgeFlipTestCase):

    def setUp(self):
        super(TestDataView, self).setUp()
        self.url = reverse('gimmick:map-data')
        self.params = {
            'fbid': 1111111, # returned by patch
            'token': 'test-token',
        }

    def test_get(self):
        response = self.client.get(self.url)
        self.assertStatusCode(response, 405)
        self.assertFalse(response.content)

    @patch_token
    @mock.patch('targetshare.tasks.ranking.px3_crawl')
    def test_post_initial(self, px3_crawl):
        px3_crawl.delay.return_value = mock.Mock(**{
            'id': 'boo',
            'ready.return_value': False,
        })

        response = self.client.post(self.url, self.params)
        self.assertStatusCode(response, 200)

        content = json.loads(response.content)
        self.assertEqual(content, {'status': 'waiting'})

        task_key = 'map_px3_task_id_{}'.format(self.params['fbid'])
        task_id = self.client.session[task_key]
        self.assertEqual(task_id, 'boo')

        # Still waiting:
        response = self.client.post(self.url, self.params)
        self.assertStatusCode(response, 200)

        content = json.loads(response.content)
        self.assertEqual(content, {'status': 'waiting'})

        self.assertEqual(self.client.session[task_key], task_id)

    @patch_facebook
    def test_post_final(self):
        # Celery is eager, so it should be done immediately:
        response = self.client.post(self.url, self.params)
        self.assertStatusCode(response, 200)

        task_key = 'map_px3_task_id_{}'.format(self.params['fbid'])
        task_id = self.client.session[task_key]
        self.assertTrue(task_id)

        content = json.loads(response.content)
        self.assertEqual(content['status'], 'success')
        self.assertEqual(set(content), {'status', 'scores'})
