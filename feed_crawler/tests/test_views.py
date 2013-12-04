import json

from mock import patch
from django.conf import settings
from django.core.urlresolvers import reverse

from targetshare.tests import EdgeFlipTestCase
from targetshare.models import dynamo


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

    @patch('feed_crawler.views.tasks.crawl_user')
    def test_subscribe_post(self, crawl_mock):
        dynamo.Token(fbid=12345, appid=1, expires=1, token='test').save()
        dynamo.Token(fbid=67890, appid=1, expires=1, token='test').save()
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
        self.assertTrue(crawl_mock.called)
        self.assertEqual(crawl_mock.call_count, 2)
        self.assertEqual(crawl_mock.call_args_list[0][0][0].fbid, 12345)
        self.assertEqual(crawl_mock.call_args_list[1][0][0].fbid, 67890)
