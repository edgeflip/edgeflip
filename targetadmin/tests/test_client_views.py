from django.core.urlresolvers import reverse

from . import TestAdminBase


class TestClientViews(TestAdminBase):

    fixtures = ['test_data']

    def test_login(self):
        self.client.logout()
        list_url = reverse('targetadmin:client-list')
        response = self.client.get(list_url)
        expected_url = reverse('targetadmin:login') + '?next=' + list_url
        self.assertRedirects(response, expected_url)

    def test_client_list(self):
        """ Test client listing """
        response = self.client.get(reverse('targetadmin:client-list'))
        self.assertStatusCode(response, 200)
        assert response.context['client_list']

    def test_client_detail(self):
        """ Test client detail view """
        response = self.client.get(reverse(
            'targetadmin:client-detail', args=[self.test_client.pk]))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['client'].name, 'mockclient')

    def test_create_new_client_get(self):
        """ Test new client view via GET"""
        response = self.client.get(reverse('targetadmin:client-new'))
        self.assertStatusCode(response, 200)
        assert response.context['form']

    def test_create_new_client_post(self):
        """ Test creating a new client object """
        response = self.client.post(reverse('targetadmin:client-new'), {
            'name': 'Test',
        })
        self.assertStatusCode(response, 302)
