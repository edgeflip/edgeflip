import json
from django.core.urlresolvers import reverse
from mock import patch

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


    fake_metrics = [
        (metric, '...', '...') for metric in
            'visits',
            'authorized_visits',
            'uniq_users_authorized',
            'visits_shown_faces',
            'visits_with_share_clicks',
            'visits_with_shares',
            'total_shares',
            'clickbacks',
    ]

    @patch('reporting.query.METRICS', fake_metrics)
    def test_client_summary(self):
        self.login_clientuser()
        response = self.client.get(reverse('reporting:client_summary', args=[1]))
        received_data = json.loads(response.content)
        expected_summary_data = {
            'visits': 4,
            'authorized_visits': 4,
            'uniq_users_authorized': 2,
            'visits_shown_faces': 3,
            'visits_with_share_clicks': 2,
            'visits_with_shares': 2,
            'total_shares': 4,
            'clickbacks': 2,
            'name': 'Specific Campaign',
            'root_id': 2,
            'first_activity': '2013-12-01',
            'latest_activity': '2013-12-01',
        }

        expected_rollup_data = {
            'visits': 4,
            'authorized_visits': 4,
            'uniq_users_authorized': 1,
            'visits_shown_faces': 3,
            'visits_with_share_clicks': 3,
            'visits_with_shares': 2,
            'total_shares': 4,
            'clickbacks': 2,
        }
        self.assertEqual(received_data['data'][0], expected_summary_data)
        self.assertEqual(received_data['rollups'][0], expected_rollup_data)


    def test_client_summary_403(self):
        self.login_clientuser()
        response = self.client.get(reverse('reporting:client_summary', args=[2]))
        self.assertStatusCode(response, 403)

    @patch('reporting.query.METRICS', fake_metrics)
    def test_campaign_hourly(self):
        self.login_clientuser()
        response = self.client.get(reverse('reporting:campaign_hourly', args=[1,2]))
        received_data = json.loads(response.content)['data']
        expected_data = [{
            'visits': 2,
            'authorized_visits': 2,
            'uniq_users_authorized': 1,
            'visits_shown_faces': 1,
            'visits_with_share_clicks': 1,
            'visits_with_shares': 1,
            'total_shares': 2,
            'clickbacks': 1,
            'time': '2013-12-01T12:00:00+00:00',
        }, {
            'visits': 2,
            'authorized_visits': 2,
            'uniq_users_authorized': 1,
            'visits_shown_faces': 2,
            'visits_with_share_clicks': 1,
            'visits_with_shares': 1,
            'total_shares': 2,
            'clickbacks': 1,
            'time': '2013-12-01T13:00:00+00:00',
        }]
        for received, expected in zip(received_data, expected_data):
            self.assertEqual(received_data, expected_data)
