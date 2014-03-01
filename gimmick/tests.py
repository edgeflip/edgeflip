import json

from django.core.urlresolvers import reverse

from targetshare.tests import EdgeFlipTestCase, patch_facebook


class TestMapView(EdgeFlipTestCase):

    def test_get(self):
        response = self.client.get(reverse('gimmick:map'))
        self.assertStatusCode(response, 200)
        self.assertTemplateUsed(response, 'gimmick/map.html')

    def test_post(self):
        response = self.client.post(reverse('gimmick:map'))
        self.assertStatusCode(response, 405)
        self.assertTemplateNotUsed(response, 'gimmick/map.html')


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

    @patch_facebook
    def test_post(self):
        response = self.client.post(self.url, self.params)
        self.assertStatusCode(response, 200)
        content = json.loads(response.content)
        self.assertEqual(content, {'status': 'waiting'})
        task_key = 'map_px3_task_id_{}'.format(self.params['fbid'])
        task_id = self.client.session[task_key]
        self.assertTrue(task_id)

        # Celery is eager, so it should be done now:
        response = self.client.post(self.url, self.params)
        self.assertStatusCode(response, 200)
        self.assertEqual(self.client.session[task_key], task_id)
        content = json.loads(response.content)
        self.assertEqual(content['status'], 'successful')
        self.assertEqual(set(content), {'status', 'scores'})
        assert 0
