import json
from django.core.urlresolvers import reverse

from . import TestReportingBase

class TestReportingViews(TestReportingBase):

    def test_main_superuser(self):
        self.login_superuser()
        response = self.client.get(reverse('reporting:main'))
        self.assertStatusCode(response, 200)
        self.assertSequenceEqual(
            response.context['clients'],
           [(1L, u'reportingclient'), (2L, u'secretclient')]
        )

    def test_main_clientuser(self):
        self.login_clientuser()
        response = self.client.get(reverse('reporting:main'))
        self.assertStatusCode(response, 200)
        self.assertEqual(len(response.context['clients']), 1)
        self.assertEqual(response.context['clients'][0], (1, 'reportingclient'))

    def test_client_summary(self):
        self.login_clientuser()
        response = self.client.get(reverse('reporting:client_summary', args=[1]))
        received_data = json.loads(response.content)
        expected_data = {
            'visits': 4,
            'clicks': 2,
            'auths': 6,
            'uniq_auths': 3,
            'shown': 10,
            'shares': 4,
            'audience': 2,
            'clickbacks': 2,
            'name': 'Specific Campaign',
            'root_id': 2,
        }
        self.assertEqual(received_data[0], expected_data)

    def test_client_summary_403(self):
        self.login_clientuser()
        response = self.client.get(reverse('reporting:client_summary', args=[2]))
        self.assertStatusCode(response, 403)

    def test_campaign_hourly(self):
        self.login_clientuser()
        response = self.client.get(reverse('reporting:campaign_hourly', args=[1,2]))
        received_data = json.loads(response.content)['data']
        expected_data = [{
            'visits': 2,
            'clicks': 1,
            'auths': 2,
            'uniq_auths': 1,
            'shown': 5,
            'shares': 2,
            'audience': 1,
            'clickbacks': 1,
            'time': '2013-12-01T12:00:00+00:00',
        }, {
            'visits': 2,
            'clicks': 1,
            'auths': 4,
            'uniq_auths': 2,
            'shown': 5,
            'shares': 2,
            'audience': 1,
            'clickbacks': 1,
            'time': '2013-12-01T13:00:00+00:00',
        }]
        for received, expected in zip(received_data, expected_data):
            self.assertEqual(received_data, expected_data)
