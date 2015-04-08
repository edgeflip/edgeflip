"""
New v2 client created for SociallyEngaged app approval.
In the future, we may merge this with targetshare or something else entirely
"""
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

from targetshare.integration.facebook import utils
from targetshare import classifier
from targetshare.models import datastructs

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
    follow_pagination = kws.pop('follow_pagination', False)

    request_path = GRAPH_ENDPOINT + '/'.join(str(part) for part in path)
    request_params = dict(kws, access_token=token, format='json')

    def background_callback(session, response):
        _handle_graph_response(response, callback, session,
                               raise_for_status=True, follow_pagination=follow_pagination, alert_next=False)

    return session.get(request_path,
                       params=request_params,
                       background_callback=background_callback)


def get_user(token):
    data = get_graph(token, 'me')
    city, state = data.get('location', {}).get('name', '').split(',')
    return datastructs.User(
        fbid=data['id'],
        fname=data['first_name'],
        lname=data['last_name'],
        email=data.get('email'),
        gender=data.get('gender'),
        birthday=data.get('birthday'),
        city=city.strip(),
        state=state.strip(),
    )


def get_taggable_friends(token):
    return [
        datastructs.TaggableFriend(
            id=data['id'],
            name=data['name'],
            picture=data['picture']['data']['url'],
        )
        for data in get_graph(token, 'me', 'taggable_friends')
    ]


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


def get_friends(access_token):
    return get_graph(access_token, 'me', 'friends')


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

    def __init__(self, user, iterable=()):
        super(Stream, self).__init__(iterable)
        self.user = user

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


    def _generate_populators(self, executor, token, permissions):
        raise NotImplementedError

    def score(self):
        raise NotImplementedError


KNOWN_ENVIRONMENTAL_PAGES = {
    1476346662580798,
    507053622651183,
    500211160069418,
    428886293805452,
    411422782296153,
    337323319689579,
    334709959913330,
    309566815767858,
    289634374392752,
    289228631144267,
    254618721275264,
    252450334805232,
    239480899433820,
    232061670199471,
    201942996498621,
    197089930443174,
    193182577358618,
    189409641073687,
    184679868223402,
    177926422264293,
    174817879203985,
    167494469941852,
    165873983447412,
    163900633655091,
    158298700898126,
    156156211117519,
    153278754738777,
    152065518140304,
    150621451650636,
    148673675293635,
    148354878566383,
    145927698751232,
    144633075722989,
    140333109359134,
    138175929718895,
    133371530009217,
    133232880058715,
    131120676911029,
    131120676911029,
    129255907131113,
    124319561009313,
    121274831221880,
    120559304621142,
    120489417993252,
    119241798126045,
    117625464977217,
    111671652210203,
    111114592238733,
    110496952324003,
    110187279004054,
    108330542521770,
    499815800211,
    455216155550,
    428908745320,
    337893980110,
    337893980110,
    322732908805,
    321088559302,
    314289124930,
    310925405807,
    295656805868,
    287683225711,
    276436719261,
    272024245003,
    254384910105,
    250187407433,
    239443018919,
    221087335084,
    216551586181,
    208876186220,
    185506013748,
    171137001336,
    166912679936,
    164389698861,
    153674637243,
    136126341809,
    133937690180,
    132594724471,
    129982267334,
    126053105675,
    124789780970,
    121247939485,
    119768100616,
    118227621359,
    111312339342,
    110761388763,
    104287844516,
    103851564652,
    102592959026,
    102535987076,
    101319218673,
    98912141410,
    94180925052,
    89151782746,
    86195995114,
    85350932978,
    80060992758,
    78368904729,
    77943343461,
    73081654186,
    71741701887,
    70090474914,
    69304610951,
    61863318139,
    60968853803,
    59420116388,
    58501419511,
    57615046615,
    54868680839,
    49402381706,
    47906709664,
    47770370187,
    39637302228,
    35601332048,
    35205934682,
    33758305054,
    33532222308,
    32904934616,
    32050048014,
    31420959864,
    28126338304,
    27532836780,
    27334917133,
    26952833476,
    25471453702,
    24526286252,
    22907478728,
    22369609145,
    21753853727,
    21631059711,
    18709174006,
    18240060318,
    17045240901,
    16477459734,
    16387505591,
    15737685211,
    15700658117,
    15687409793,
    14413545701,
    12410115279,
    12220731247,
    12185972707,
    12155623289,
    11791104453,
    11111618026,
    9079518250,
    8914040942,
    8895898655,
    8492293163,
    8422338499,
    8057376739,
    8057376739,
    8002590959,
    7962229886,
    7785276338,
    7341997111,
    6204742571,
    5720973755,
    5644748986,
    5435784683,
}

MAYBE_ENVIRONMENTAL_CATEGORIES = {
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
}

DEFINITELY_ENVIRONMENTAL_SUBCATEGORIES = {
    'Eco Tours',
    'Environmental Conservation',
    'Environmental Consultant',
    'National Park',
    'Solar Energy Service',
    'State Park',
    'Wildlife Sanctuary',
    'Zoo & Aquarium',
}

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
                if page.page_id in KNOWN_ENVIRONMENTAL_PAGES:
                    self.append(page)
                else:
                    if page.category in MAYBE_ENVIRONMENTAL_CATEGORIES:
                        data = get_graph(token, page.page_id, fields="category_list")
                        if any(cat['name'] in DEFINITELY_ENVIRONMENTAL_SUBCATEGORIES for cat in data.get('category_list', [])):
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

    def _generate_populators(self, executor, token, permissions):
        session = requests_futures.sessions.FuturesSession(executor=executor)
        session.mount(GRAPH_ENDPOINT, requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES))

        for days_back in xrange(0, DAYS_BACK, DAY_CHUNK_SIZE):
            if self.permission in permissions:
                end_time = time.mktime((datetime.datetime.today() - datetime.timedelta(days=days_back)).timetuple())
                start_time = time.mktime((datetime.datetime.today() - datetime.timedelta(days=days_back+DAY_CHUNK_SIZE)).timetuple())
                yield get_graph_future(session, token, 'me', self.endpoint,
                                       since=start_time,
                                       until=end_time,
                                       follow_pagination=True,
                                       callback=self._handle_response)

    def _handle_response(self, data, _response, _session):
        for post in self.xread(data):
            if post.message:
                topics = classifier.classify(
                    post.message,
                    'Environment',
                )
                if topics.get('Environment', 0) > 0:
                    self.append(post._replace(score=topics['Environment']))


    def score(self):
        return sum(post.score for post in self)
