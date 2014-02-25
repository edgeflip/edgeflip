import json
import os.path
import random
import re
import urllib

import faraday
import us
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone
from mock import Mock, patch

from targetshare import models
from targetshare.tasks.ranking import FilteringResult, empty_filtering_result


DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


class EdgeFlipTestCase(TestCase):

    global_patches = (
        patch('django.conf.settings.CELERY_ALWAYS_EAGER', True),
        patch.multiple(
            faraday.conf.settings,
            PREFIX='test',
            LOCAL_ENDPOINT='localhost:4444',
        ),
    )

    @classmethod
    def setUpClass(cls):
        for patch_ in cls.global_patches:
            patch_.start()

        # In case a bad test class doesn't clean up after itself:
        faraday.db.destroy(confirm=False)

    @classmethod
    def tearDownClass(cls):
        for patch_ in cls.global_patches:
            patch_.stop()

    def setUp(self):
        super(EdgeFlipTestCase, self).setUp()
        faraday.db.build()

    def tearDown(self):
        faraday.db.destroy(confirm=False)
        super(EdgeFlipTestCase, self).tearDown()

    def assertStatusCode(self, response, status=200):
        self.assertEqual(response.status_code, status)


class EdgeFlipViewTestCase(EdgeFlipTestCase):

    def setUp(self):
        super(EdgeFlipViewTestCase, self).setUp()
        self.params = {
            'fbid': '1',
            'token': 1,
            'num_face': 9,
            'sessionid': 'fake-session',
            'campaign': 1,
            'content': 1,
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
        self.test_edge = models.datastructs.UserNetwork.Edge(
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
            px3_result_mock.result = FilteringResult(
                [self.test_edge],
                models.datastructs.TieredEdges(
                    edges=[self.test_edge],
                    campaign_id=1,
                    content_id=1,
                ),
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
            px4_result_mock.result = (
                empty_filtering_result._replace(ranked=[self.test_edge])
                if px4_successful else error)
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


FIRST_NAMES = ('Larry', 'Darryl', 'Darryl', 'Bob', 'Bart', 'Lisa', 'Maggie',
               'Homer', 'Marge', 'Dude', 'Jeffrey', 'Keyser', 'Ilsa')
LAST_NAMES = ('Newhart', 'Simpson', 'Lebowski', 'Soze', 'Lund', 'Smith', 'Doe')
CITY_NAMES = ('Casablanca', 'Sprinfield', 'Shelbyville', 'Nowhere', 'Capital City')


def fake_user(fbid, friend=False, num_friends=0):
    fake = {
        'uid': fbid,
        'sex': u'male' if random.random() < 0.5 else u'female',
        'first_name': random.choice(FIRST_NAMES),
        'last_name': random.choice(LAST_NAMES),
    }

    if random.random() <= 0.33:
        fake['birthday_date'] = '%s/%s/%s' % (
            random.randint(1, 12),
            random.randint(1, 28),
            random.randint(1920, 1995),
        )
    else:
        fake['birthday_date'] = None

    if random.random() <= 0.67:
        fake['current_location'] = {
            'city': random.choice(CITY_NAMES),
            'state': random.choice(us.STATES_AND_TERRITORIES).name,
        }

    if friend:
        # Only have a mutual friend count for friends
        fake['mutual_friend_count'] = random.randint(0, num_friends)
    else:
        # Only get an email for primaries
        fake['email'] = u'fake@fake.com'

    return fake


def crawl_mock(min_friends, max_friends, closure=None):
    fake_fbids = tuple({100000000000 + random.randint(1, 10000000)
                        for _ in xrandrange(min_friends, max_friends)})
    friend_count = len(fake_fbids)
    synchronous_results = iter([])

    dir_ = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(dir_)
    corpus = open(os.path.join(os.path.dirname(app_dir), 'README.md')).read()
    words = re.split(r'\s+', corpus)

    def urlopen_mock(url):
        # First two calls are synchronous, should just return these:
        try:
            return next(synchronous_results)
        except StopIteration:
            pass

        # Threaded results:
        if 'from+stream' in url.lower():
            # StreamReaderThread
            data = {
                'stream': [],
                'post_likes': [],
                'post_comms': [],
                'stat_likes': [],
                'stat_comms': [],
                'wall_posts': [],
                'wall_comms': [],
                'tags': [],
            }
            for post_id0 in xrandrange(2, 20, 1):
                post_id = '1_{}'.format(post_id0)
                start = random.randint(0, len(words))
                end = random.randint(start, len(words))
                message = ' '.join(words[start:end])
                data['stream'].append({'post_id': post_id,
                                       'message': message})
                for column in data:
                    if column == 'stream' or (random.randint(1, 50) % 50):
                        # This is the stream field,
                        # or only give others 1 in 50 chance of representation
                        continue
                    if column == 'tags':
                        user_ids = random.sample(fake_fbids, random.randint(1, 2))
                    else:
                        user_ids = random.choice(fake_fbids)
                    column_data = {'post_id': post_id}
                    column_data['user_id'] = column_data['fromid'] = \
                        column_data['actor_id'] = column_data['tagged_ids'] = \
                        user_ids
                    data[column].append(column_data)
            return {'data': [
                {'name': entry_type, 'fql_result_set': result_set}
                for (entry_type, result_set) in data.items()
            ]}

        elif 'friend_count+from' in url.lower():
            return {'data': [{'friend_count': friend_count}]}

        elif 'from+user' in url.lower():
            if "select+uid%2c+first_name%2c+last_name" in url.lower():
                # User info
                return {'data': [fake_user(1)]}

            # Friend info
            return {'data': [fake_user(fbid, friend=True, num_friends=friend_count)
                             for fbid in fake_fbids]}

        elif 'from+photo' in url.lower():
            # Photo info
            return {'data': [
                {'name': 'primPhotoTags',
                 'fql_result_set': [{'subject': str(random.choice(fake_fbids))} for _ in xrandrange(0, 500)]},
                {'name': 'otherPhotoTags',
                 'fql_result_set': [{'subject': str(random.choice(fake_fbids))} for _ in xrandrange(0, 25000)]},
                {'name': 'friendInfo',
                 'fql_result_set': [fake_user(fbid, friend=True, num_friends=friend_count)
                                    for fbid in fake_fbids]},
            ]}

        elif closure:
            return closure(url)
        else:
            raise RuntimeError("No mock for URL: {}".format(url))

    # mock to be patched on urllib2.urlopen:
    return Mock(side_effect=lambda url, timeout=None:
        Mock(**{'read.return_value': json.dumps(urlopen_mock(url))})
    )


def patch_facebook(func=None, min_friends=1, max_friends=1000, closure=None):
    patches = (
        patch(
            'targetshare.integration.facebook.client.urllib2.urlopen',
            crawl_mock(min_friends, max_friends, closure)
        ),
        patch('targetshare.integration.facebook.client.extend_token', Mock(
            return_value=models.dynamo.Token(
                token='test-token',
                fbid=1111111,
                appid=471727162864364,
                expires=timezone.now(),
            )
        )),
    )

    def decorator(func):
        for facebook_patch in patches:
            func = facebook_patch(func)
        return func

    if func:
        return decorator(func)
    else:
        return decorator
