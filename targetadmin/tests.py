from django.core.urlresolvers import reverse

from targetshare.tests import EdgeFlipTestCase
from targetshare.models import relational


class TargetAdminTest(EdgeFlipTestCase):

    fixtures = ['targetadmin_test_data']

    def setUp(self):
        super(TargetAdminTest, self).setUp()
        self.test_client = relational.Client.objects.create(
            name='Testing Client',
            _fb_app_id=1234,
            _fb_app_name='That One App',
            domain='example.com',
            subdomain='test',
        )
        self.test_content = relational.ClientContent.objects.create(
            name='Testing Content',
            client=self.test_client
        )
        assert self.client.login(
            username='tester',
            password='testing',
        )

    def test_client_list(self):
        """ Test client listing """
        response = self.client.get(reverse('client-list'))
        self.assertStatusCode(response, 200)
        assert response.context['client_list']

    def test_client_detail(self):
        """ Test client detail view """
        response = self.client.get(reverse('client-detail', args=[1]))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['client'].name, 'Testing Client')

    def test_create_new_client_get(self):
        """ Test new client view via GET"""
        response = self.client.get(reverse('client-new'))
        self.assertStatusCode(response, 200)
        assert response.context['form']

    def test_create_new_client_post(self):
        """ Test creating a new client object """
        response = self.client.post(reverse('client-new'), {
            'name': 'Test',
        })
        self.assertStatusCode(response, 302)

    def test_content_list_view(self):
        ''' Test viewing a content list '''
        response = self.client.get(
            reverse('content-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_content_detail_view(self):
        ''' Test viewing a content object '''
        response = self.client.get(
            reverse('content-detail', args=[self.test_client.pk, self.test_content.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object']

    def test_content_detail_invalid_client(self):
        ''' Test viewing a content object with a non-matching client '''
        new_client = relational.Client.objects.create(name='No good')
        response = self.client.get(
            reverse('content-detail', args=[new_client.pk, self.test_content.pk])
        )
        self.assertStatusCode(response, 404)

    def test_create_new_content_object(self):
        ''' Create a new content object '''
        response = self.client.post(
            reverse('content-new', args=[self.test_client.pk]),
            {'name': 'New Content', 'client': self.test_client.pk}
        )
        self.assertStatusCode(response, 302)
        obj = relational.ClientContent.objects.get(
            client=self.test_client,
            name='New Content'
        )
        self.assertRedirects(
            response,
            reverse('content-detail', args=[self.test_client.pk, obj.pk])
        )
