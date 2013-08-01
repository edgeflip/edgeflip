import json
from datetime import date

from django.conf import settings
from django.core.urlresolvers import reverse

from mock import patch, Mock

from targetshare import datastructs, models, client_db_tools as cdb
from targetshare.tests import EdgeFlipTestCase


class TestEdgeFlipViews(EdgeFlipTestCase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestEdgeFlipViews, self).setUp()
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
        self.test_client = models.Client.objects.get(pk=1)
        self.test_cs = models.ChoiceSet.objects.create(
            client=self.test_client, name='Unit Tests')
        self.test_filter = models.ChoiceSetFilter.objects.create(
            filter_id=2, url_slug='all', choice_set=self.test_cs)

        # mock mock_mode subdomain
        self.orig_subdomain = settings.WEB.mock_subdomain
        settings.WEB.mock_subdomain = 'testserver'

    def tearDown(self):
        settings.WEB.mock_subdomain = self.orig_subdomain
        super(TestEdgeFlipViews, self).tearDown()

    def test_faces_get(self):
        ''' Faces endpoint requires POST, so we expect a 405 here '''
        response = self.client.get(reverse('faces'))
        self.assertStatusCode(response, 405)

    def test_faces_initial_entry(self):
        ''' Tests a users first request to the Faces endpoint. We expect to
        receive a JSON response with a status of waiting along with the
        tasks IDs of the Celery jobs we started
        '''
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        assert data['px3_task_id']
        assert data['px4_task_id']

    def test_faces_invalid_subdomain(self):
        ''' Test hitting the faces endpoint from an invalid domain '''
        self.test_client.subdomain = 'invalidsubdomain'
        self.test_client.save()
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 404)

    @patch('targetshare.views.celery')
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
        celery_mock.current_app.AsyncResult = async_mock
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid'
        })
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'waiting')

    @patch('targetshare.views.celery')
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
        celery_mock.current_app.AsyncResult = async_mock
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid'
        })
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'waiting')

    @patch('targetshare.views.celery')
    def test_faces_last_call(self, celery_mock):
        ''' Test that gives up on waiting for the px4 result, and serves the
        px3 results
        '''
        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = True
        px3_result_mock.result = (
            [self.test_edge],
            cdb.TieredEdges(edges=[self.test_edge], campaignId=1, contentId=1),
            self.test_filter.filter_id,
            self.test_filter.url_slug,
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
        celery_mock.current_app.AsyncResult = async_mock
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid',
            'last_call': True,
        })
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        assert data['html']

    @patch('targetshare.views.celery')
    def test_faces_complete_crawl(self, celery_mock):
        ''' Test that completes both px3 and px4 crawls '''
        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = True
        px3_result_mock.result = (
            [self.test_edge],
            cdb.TieredEdges(edges=[self.test_edge], campaignId=1, contentId=1),
            self.test_filter.filter_id,
            self.test_filter.url_slug,
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
        celery_mock.current_app.AsyncResult = async_mock
        self.params.update({
            'px3_task_id': 'dummypx3taskid',
            'px4_task_id': 'dummypx4taskid',
            'last_call': True,
        })
        response = self.client.post(reverse('faces'), data=self.params)
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        assert data['html']
