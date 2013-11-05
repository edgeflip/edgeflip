import json
import os.path
import random
import urllib
import urllib2

from mock import Mock, patch

from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from pymlconf import ConfigDict

from targetshare import models
from targetshare.integration.facebook import mock_client
from targetshare.models.dynamo import utils


DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


class EdgeFlipTestCase(TestCase):

    def setUp(self):
        super(EdgeFlipTestCase, self).setUp()

        # Test settings:
        self.patches = []
        self.patches.append(
            patch.multiple(
                settings,
                CELERY_ALWAYS_EAGER=True,
                DYNAMO=ConfigDict({'prefix': 'test', 'engine': 'mock', 'port': 4444}),
            )
        )
        # Dynamo tables are created eagerly; force reset of prefix:
        for table in utils.database.tables:
            self.patches.append(
                patch.object(table, 'table_name', table.short_name)
            )
        # Start patches:
        for p in self.patches:
            p.start()

        # Restore dynamo data:
        utils.database.drop_all_tables() # drop if exist
        utils.database.create_all_tables()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        super(EdgeFlipTestCase, self).tearDown()

    def assertStatusCode(self, response, status=200):
        self.assertEqual(response.status_code, status)


class EdgeFlipViewTestCase(EdgeFlipTestCase):

    def setUp(self):
        super(EdgeFlipViewTestCase, self).setUp()
        self.params = {
            'fbid': '1',
            'token': 1,
            'num': 9,
            'sessionid': 'fake-session',
            'campaignid': 1,
            'contentid': 1,
        }
        self.test_user = models.User(
            fbid=1,
            fname='Test',
            lname='User',
            email='test@example.com',
            gender='male',
            birthday=timezone.datetime(1984, 1, 1, tzinfo=timezone.utc),
            city='Chicago',
            state='Illinois',
        )
        self.test_edge = models.datastructs.Edge(
            self.test_user,
            self.test_user,
            None
        )
        self.test_client = models.Client.objects.get(pk=1)
        self.test_cs = models.ChoiceSet.objects.create(
            client=self.test_client, name='Unit Tests')
        self.test_filter = models.ChoiceSetFilter.objects.create(
            filter_id=2, url_slug='all', choice_set=self.test_cs)

    def get_outgoing_url(self, redirect_url, campaign_id=None):
        if campaign_id:
            qs = '?' + urllib.urlencode({'campaignid': campaign_id})
        else:
            qs = ''
        url = reverse('outgoing', args=[self.test_client.fb_app_id,
                                         urllib.quote_plus(redirect_url)])
        return url + qs

    def patch_ranking(self, celery_mock,
                      px3_ready=True, px3_successful=True,
                      px4_ready=True, px4_successful=True):
        if px3_ready:
            px3_failed = not px3_successful
        else:
            px3_successful = px3_failed = False

        if px4_ready:
            px4_failed = not px4_successful
        else:
            px4_successful = px4_failed = False

        error = ValueError('Ruh-Roh!')

        px3_result_mock = Mock()
        px3_result_mock.ready.return_value = px3_ready
        px3_result_mock.successful.return_value = px3_successful
        px3_result_mock.failed.return_value = px3_failed
        if px3_ready:
            px3_result_mock.result = (
                [self.test_edge],
                models.datastructs.TieredEdges(edges=[self.test_edge], campaignId=1, contentId=1),
                self.test_filter.filter_id,
                self.test_filter.url_slug,
                1,
                1
            ) if px3_successful else error
        else:
            px3_result_mock.result = None

        px4_result_mock = Mock()
        px4_result_mock.ready.return_value = px4_ready
        px4_result_mock.successful.return_value = px4_successful
        px4_result_mock.failed.return_value = px4_failed
        if px4_ready:
            px4_result_mock.result = [self.test_edge] if px4_successful else error
        else:
            px4_result_mock.result = None

        async_mock = Mock()
        async_mock.side_effect = [
            px3_result_mock,
            px4_result_mock
        ]
        celery_mock.current_app.AsyncResult = async_mock


def xrandrange(min_=0, max_=None, start=0, step=1):
    if max_ is None:
        raise TypeError
    return xrange(start, random.randint(min_, max_), step)


def crawl_mock():
    fake_fbids = tuple(set(100000000000 + random.randint(1, 10000000)
                       for _ in xrandrange(1, 1000)))
    friend_count = len(fake_fbids)
    synchronous_results = iter([
        # get_user:
        {'data': [mock_client.fakeUserInfo(1)]},
        # get_friend_edges:
        {'data': [{'friend_count': friend_count}]},
    ])

    def urlopen_mock(url):
        # First two calls are synchronous, should just return these:
        try:
            return next(synchronous_results)
        except StopIteration:
            pass

        # Threaded results:
        if isinstance(url, urllib2.Request):
            # ThreadStreamReader
            data = [
                {'name': 'tags', 'fql_result_set': [{'tagged_ids': list(xrandrange(0, 25, 1))}
                                                    for _ in xrandrange(0, 25)]},
                {'name': 'stream', 'fql_result_set': []},
            ] + [
                {'name': column, 'fql_result_set': [dict.fromkeys(['user_id', 'fromid', 'actor_id'], value)
                                                for value in xrandrange(0, 25, 1)]}
                for column in (
                    'postLikes',
                    'postComms',
                    'statLikes',
                    'statComms',
                    'wallPosts',
                    'wallComms',
                )
            ]
            return {'data': data}

        elif 'from+user' in url.lower():
            # Friend info
            return {'data': [mock_client.fakeUserInfo(fbid, friend=True, numFriends=friend_count)
                             for fbid in fake_fbids]}

        elif 'from+photo' in url.lower():
            # Photo info
            return {'data': [
                {'name': 'primPhotoTags',
                 'fql_result_set': [{'subject': str(random.choice(fake_fbids))} for _ in xrandrange(0, 500)]},
                {'name': 'otherPhotoTags',
                 'fql_result_set': [{'subject': str(random.choice(fake_fbids))} for _ in xrandrange(0, 25000)]},
                {'name': 'friendInfo',
                 'fql_result_set': [mock_client.fakeUserInfo(fbid, friend=True, numFriends=friend_count)
                                    for fbid in fake_fbids]},
            ]}

    # mock to be patched on urllib2.urlopen:
    return Mock(side_effect=lambda url, timeout=None:
        Mock(**{'read.return_value': json.dumps(urlopen_mock(url))})
    )


def patch_facebook(func=None):
    patches = (
        patch('targetshare.integration.facebook.client.urllib2.urlopen', crawl_mock()),
        patch('targetshare.integration.facebook.client.extend_token', Mock(
            return_value=models.dynamo.Token(
                token='test-token',
                fbid=1111111,
                appid=471727162864364,
                expires=timezone.now(),
            )
        )),
    )
    if func:
        for facebook_patch in patches:
            func = facebook_patch(func)
        return func
    return patches
