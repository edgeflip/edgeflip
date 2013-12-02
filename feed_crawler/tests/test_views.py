import json

from django.conf import settings
from django.core.urlresolvers import reverse

from targetshare.tests import EdgeFlipTestCase


class TestFeedCrawlerViews(EdgeFlipTestCase):

    def test_subscribe_get_forbidden(self):
        response = self.client.get(reverse('realtime-subscription'))
        self.assertStatusCode(response, 403)

    def test_subscribe_get(self):
        response = self.client.get(reverse('realtime-subscription'), {
            'hub.mode': 'subscribe',
            'hub.challenge': 'this is a test',
            'hub.verify_token': settings.FB_REALTIME_TOKEN,
        })
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response.content,
            'this is a test'
        )

    def test_subscribe_post(self):
        response = self.client.post(reverse('realtime-subscription'),
            dict(data=json.dumps({
                "object": "feed",
                "entry": [
                    {"uid": 12345},
                    {"uid": 67890},
                ]
            }))
        )
        self.assertStatusCode(response, 200)
