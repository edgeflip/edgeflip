import json

from django.core.urlresolvers import reverse

from . import TestAdminBase


class TestClientViews(TestAdminBase):

    fixtures = ['admin_test_data']

    def test_login(self):
        self.client.logout()
        list_url = reverse('targetadmin:client-list')
        response = self.client.get(list_url)
        expected_url = reverse('targetadmin:login') + '?next=' + list_url
        self.assertRedirects(response, expected_url)

    def test_client_list(self):
        """ Test client listing """
        response = self.client.get(reverse('targetadmin:client-list'))
        self.assertStatusCode(response, 302)

    def test_client_detail(self):
        """ Test client detail view """
        response = self.client.get(reverse('targetadmin:client-detail',
                                           args=[self.test_client.pk]))
        self.assertStatusCode(response, 200)

        client = response.context['client']
        self.assertEqual(client.name, 'mockclient')

        campaigns = json.loads(response.context['campaigns'])
        self.assertTrue(campaigns)
        self.assertEqual(campaigns[0], {
            'pk': 1,
            'name': 'Gun Control',
            'create_dt': '2013-07-15T16:38:28Z',
            'campaign_properties': {'status': 'draft'},
        })
