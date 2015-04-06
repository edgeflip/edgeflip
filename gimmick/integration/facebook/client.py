"""Facebook API v2 client"""
import collections
import datetime
import enum
import logging
import sys
import time
from concurrent import futures

import requests
import requests_futures.sessions
from django.conf import settings

from core.utils.version import make_version

from targetshare import utils
from targetshare import classifier

LOG = logging.getLogger(__name__)

API_VERSION = make_version('2.3')

GRAPH_ENDPOINT = 'https://graph.facebook.com/v{}/'.format(API_VERSION)

DAY_CHUNK_SIZE = settings.FACEBOOK.stream.get('day_chunk_size', 30)
DAYS_BACK = settings.FACEBOOK.stream.get('days_back', 180)
PAGE_CHUNK_SIZE = settings.FACEBOOK.stream.get('page_chunk_size', 20)
NUM_PAGES = settings.FACEBOOK.stream.get('num_pages', 100)
MAX_WAIT = settings.FACEBOOK.stream.get('max_wait', 15)

MAX_RETRIES = 3
THREAD_COUNT = 6


@enum.unique
class Permissions(str, enum.Enum):

    PUBLIC_PROFILE = 'public_profile'
    USER_FRIENDS = 'user_friends'
    EMAIL = 'email'
    USER_BIRTHDAY = 'user_birthday'
    USER_LOCATION = 'user_location'
    USER_POSTS = 'user_posts'
    USER_LIKES = 'user_likes'


def _handle_graph_response(response, callback=None, session=None,
                           raise_for_status=False, follow_pagination=True, alert_next=True):
    if raise_for_status:
        response.raise_for_status()

    payload = response.json()
    keys = tuple(payload)
    if 'paging' in keys or keys == ('data',):
        data = payload['data']
        next_ = payload.get('paging', {}).get('next')
        if next_:
            if follow_pagination:
                data.extend(_get_graph(next_))
            elif alert_next:
                LOG.info("Will not traverse pagination: %r", next_)
    else:
        data = payload

    if callback is None:
        return data

    return callback(data, response, session)


def _handle_graph_exception(exc):
    response = getattr(exc, 'response', None)
    request = getattr(response, 'request', None)
    reason = getattr(response, 'reason', '')
    content = getattr(response, 'content', '')
    url = getattr(request, 'url', '')

    if isinstance(exc, (IOError, RuntimeError)):
        LOG.warning("Error opening Graph URL [%s] %s(%r): %s",
                    url,
                    exc.__class__.__name__,
                    reason,
                    content,
                    exc_info=True)
    else:
        LOG.exception("Error in request: %s", exc)

    if hasattr(sys, 'exc_value'):
        # If we're already in the middle of exception-handling,
        # raise exception of appropriate type:
        if content:
            utils.OAuthException.raise_for_response(content)
        raise


def _request_graph(method, path, params=None, data=None):
    try:
        response = requests.request(method, path, data=data, params=params)
        response.raise_for_status()
    except (IOError, RuntimeError) as exc:
        _handle_graph_exception(exc)

    return response


def _get_graph(path, params=None):
    return _handle_graph_response(_request_graph('get', path, params))


def get_graph(token, *path, **fields):
    request_path = GRAPH_ENDPOINT + '/'.join(str(part) for part in path)
    request_params = dict(fields, access_token=token, format='json')
    return _get_graph(request_path, request_params)


def get_graph_future(session, token, *path, **kws):
    callback = kws.pop('callback', None)

    request_path = GRAPH_ENDPOINT + '/'.join(str(part) for part in path)
    request_params = dict(kws, access_token=token, format='json')

    def background_callback(session, response):
        _handle_graph_response(response, callback, session,
                               raise_for_status=True, follow_pagination=False, alert_next=False)

    return session.get(request_path,
                       params=request_params,
                       background_callback=background_callback)


def post_graph(token, *path, **kws):
    request_path = GRAPH_ENDPOINT + '/'.join(str(part) for part in path)
    request_params = dict(kws.get('params', ()), access_token=token, format='json')
    request_data = kws.get('data')
    response = _request_graph('post', request_path, params=request_params, data=request_data)
    return response.json()


def post_notification(app_token, fbid, href, template, ref=None):
    request_params = {'href': href, 'template': template}
    if ref is not None:
        request_params['ref'] = ref
    payload = post_graph(app_token, fbid, 'notifications', params=request_params)
    return payload['success']


class Stream(list):

    REPR_OUTPUT_SIZE = 5

    @classmethod
    def read(cls, user, token, permissions=Permissions):
        """Construct a new Stream for the given User from the Facebook Graph API."""
        stream = cls(user)

        # Populate Stream.Posts in separate worker threads
        with futures.ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
            futures_iter = stream._generate_populators(executor, token, permissions)

            try:
                for done_future in futures.as_completed(tuple(futures_iter), MAX_WAIT):
                    exc = done_future.exception()
                    if exc:
                        # In development, put `done_future.result()` here
                        # to raise exception in main thread.
                        _handle_graph_exception(exc)
            except futures.TimeoutError as exc:
                LOG.warning(
                    "Could not retrieve Facebook data in time (%ss)", MAX_WAIT,
                    exc_info=True
                )

        return stream

    def __iadd__(self, other):
        if self.user != other.user:
            raise ValueError("Streams belong to different users")
        self.extend(other)
        return self

    def __add__(self, other):
        new = type(self)(self.user, self)
        new += other
        return new

    def __repr__(self):
        data = list(self[:self.REPR_OUTPUT_SIZE + 1])
        if len(data) > self.REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return "{}({!r}, {!r})".format(self.__class__.__name__,
                                       self.user,
                                       data)
    def score(self):
        return 0.2


MAYBE_ENVIRONMENTAL_CATEGORIES = set([
    'Attractions/things to do',
    'Cause',
    'Community organization',
    'Community/government',
    'Education',
    'Farming/agriculture',
    'Landmark',
    'Local Business',
    'Museum/art gallery',
    'Non-governmental organization (ngo)',
    'Non-profit organization',
    'Organization',
    'Public places',
])

DEFINITELY_ENVIRONMENTAL_SUBCATEGORIES = set([
    'Eco Tours',
    'Environmental Conservation',
    'Environmental Consultant',
    'National Park',
    'Solar Energy Service',
    'State Park',
    'Wildlife Sanctuary',
    'Zoo & Aquarium',
])

Page = collections.namedtuple('Page', ('page_id', 'name', 'category'))

class LikeStream(Stream):
    permission = Permissions.USER_LIKES
    endpoint = 'likes'

    @staticmethod
    def xread(data):
        """Iteratively construct stream from a structured Facebook API response."""
        for datum in data:
            page = Page(
                page_id=datum['id'],
                name=datum.get('name', ''),
                category=datum.get('category', ''),
            )
            yield page

    def __init__(self, user, iterable=()):
        super(LikeStream, self).__init__(iterable)
        self.user = user

    def _generate_populators(self, executor, token, permissions):
        session = requests_futures.sessions.FuturesSession(executor=executor)
        session.mount(GRAPH_ENDPOINT, requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES))

        for offset in xrange(0, NUM_PAGES, PAGE_CHUNK_SIZE):
            if self.permission in permissions:
                yield get_graph_future(session, token, 'me', self.endpoint,
                                       limit=PAGE_CHUNK_SIZE,
                                       offset=offset,
                                       callback=self._callback(token))

    def _callback(self, token):
        def callback(data, response, session):
            pages = self.xread(data)
            for page in pages:
                if page.category in MAYBE_ENVIRONMENTAL_CATEGORIES:
                    data = get_graph(token, page.page_id, fields="category_list")
                    if any(cat['name'] in DEFINITELY_ENVIRONMENTAL_SUBCATEGORIES for cat in data.get('category_list', [])):
                        print "Page", page, "is environmental"
                        self.append(page)

        return callback

    def score(self):
        return 0.2*len(self)


Post = collections.namedtuple('Post', ('post_id', 'message', 'score'))

class PostStream(Stream):
    permission = Permissions.USER_POSTS
    endpoint = 'feed'


    @staticmethod
    def xread(data):
        for datum in data:
            post = Post(
                post_id=datum['id'],
                message=datum.get('message', ''),
                score=0,
            )

            yield post

    def __init__(self, user, iterable=()):
        super(PostStream, self).__init__(iterable)
        self.user = user

    def _generate_populators(self, executor, token, permissions):
        session = requests_futures.sessions.FuturesSession(executor=executor)
        session.mount(GRAPH_ENDPOINT, requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES))

        for days_back in xrange(0, DAYS_BACK, DAY_CHUNK_SIZE):
            if self.permission in permissions:
                end_time = time.mktime((datetime.datetime.today() - datetime.timedelta(days=days_back)).timetuple())
                start_time = time.mktime((datetime.datetime.today() - datetime.timedelta(days=days_back+DAY_CHUNK_SIZE)).timetuple())
                yield get_graph_future(session, token, 'me', self.endpoint,
                                       limit=DAY_CHUNK_SIZE,
                                       since=start_time,
                                       until=end_time,
                                       callback=self._callback(token))

    def _callback(self, token):
        def callback(data, response, session):
            posts = self.xread(data)
            for post in posts:
                if post.message:
                    topics = classifier.classify(
                        post.message,
                        'Environment',
                    )
                    if topics.get('Environment', 0) > 0:
                        self.append(post._replace(score=topics['Environment']))

        return callback

    def score(self):
        return sum(post.score for post in self)
