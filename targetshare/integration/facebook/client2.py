"""Facebook API v2 client"""
import collections
import enum
import logging
import sys
from concurrent import futures

import requests
import requests_futures.sessions
from django.conf import settings

from core.utils.version import make_version

from targetshare.models import datastructs

from . import utils


LOG = logging.getLogger(__name__)

API_VERSION = make_version('2.2')

GRAPH_ENDPOINT = 'https://graph.facebook.com/v{}/'.format(API_VERSION)

NUM_POSTS = settings.FACEBOOK.stream.get('num_posts', 100)
CHUNK_SIZE = settings.FACEBOOK.stream.get('chunk_size', 20)
MAX_WAIT = settings.FACEBOOK.stream.get('max_wait', 15)

MAX_RETRIES = 3
THREAD_COUNT = 6


@enum.unique
class Permissions(str, enum.Enum):

    PUBLIC_PROFILE = 'public_profile'
    USER_FRIENDS = 'user_friends'
    EMAIL = 'email'
    USER_ACTIVITIES = 'user_activities'
    USER_BIRTHDAY = 'user_birthday'
    USER_LOCATION = 'user_location'
    USER_INTERESTS = 'user_interests'
    USER_LIKES = 'user_likes'
    USER_PHOTOS = 'user_photos'
    USER_RELATIONSHIPS = 'user_relationships'
    USER_STATUS = 'user_status'
    USER_VIDEOS = 'user_videos'


def _handle_graph_response(response, callback=None, session=None, raise_for_status=False, alert_next=False):
    if raise_for_status:
        response.raise_for_status()

    payload = response.json()
    keys = tuple(payload)
    if 'paging' in keys or keys == ('data',):
        # TODO: handle paging
        next_ = payload.get('paging', {}).get('next')
        if alert_next and next_:
            LOG.error("Will not traverse pagination: %r", next_)
        data = payload['data']
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


def get_graph(token, *path, **fields):
    request_path = GRAPH_ENDPOINT + '/'.join(str(part) for part in path)
    request_params = dict(fields, access_token=token, format='json')

    try:
        response = requests.get(request_path, params=request_params)
        response.raise_for_status()
    except (IOError, RuntimeError) as exc:
        _handle_graph_exception(exc)

    return _handle_graph_response(response, alert_next=True)


def get_graph_future(session, token, *path, **kws):
    callback = kws.pop('callback', None)

    request_path = GRAPH_ENDPOINT + '/'.join(str(part) for part in path)
    request_params = dict(kws, access_token=token, format='json')

    def background_callback(session, response):
        _handle_graph_response(response, callback, session, raise_for_status=True)

    return session.get(request_path,
                       params=request_params,
                       background_callback=background_callback)


def get_user(token):
    data = get_graph(token, 'me')
    return datastructs.User(
        fbid=data['id'],
        fname=data['first_name'],
        lname=data['last_name'],
        email=data.get('email'),
        gender=data.get('gender'),
        # TODO?:
        # birthday=utils.decode_date(data.get('birthday')),
        # bio=data.get('bio', '')[:150],
        # city=location.get('city'),
        # state=location.get('state'),
        # country=location.get('country'),
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


def get_friend_edges(token):
    """Read the user's Stream and compute their IncomingEdges."""
    user = get_user(token)
    stream = Stream.read(user, token)
    return stream.get_friend_edges()


Post = collections.namedtuple('Post', ('post_id', 'message', 'interactions'))
Interaction = collections.namedtuple('Interaction', ('user_id', 'name', 'type'))


class UserAggregate(object):

    __slots__ = ('uid', 'name', 'types')

    def __init__(self, uid, name, types=None):
        self.uid = uid
        self.name = name
        self.types = collections.defaultdict(int) if types is None else types

    def increment(self, type_):
        self.types[type_] += 1

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(
            self.__class__.__name__,
            self.uid,
            self.name,
            dict(self.types),
        )


class Stream(list):

    REPR_OUTPUT_SIZE = 5

    @staticmethod
    def xreadposts(data, post_type):
        """Iteratively construct Stream.Posts from a structured Facebook API response."""
        for datum in data:
            post = Post(
                post_id=datum['id'],
                message=datum.get('message', ''),
                interactions=[]
            )

            # Photo/video
            if post_type in ('photo', 'video') and 'from' in datum:
                user = datum['from']
                action_type = '{}s_target'.format(post_type)
                post.interactions.append(
                    Interaction(user['id'], user['name'], action_type)
                )

            # Tags
            for user in datum.get('tags', {}).get('data', ()):
                if 'id' not in user:
                    continue

                action_type = post_type + '_tags'
                post.interactions.append(
                    Interaction(user['id'], user['name'], action_type)
                )
                if 'place' in datum:
                    post.interactions.append(
                        Interaction(user['id'], user['name'], 'place_tags')
                    )

            # Likes
            for user in datum.get('likes', {}).get('data', ()):
                action_type = post_type + '_likes'
                post.interactions.append(
                    Interaction(user['id'], user['name'], action_type)
                )

            # Comments
            for comment in datum.get('comments', {}).get('data', ()):
                user = comment['from']
                action_type = post_type + '_comms'
                post.interactions.append(
                    Interaction(user['id'], user['name'], action_type)
                )

            yield post

    def _make_response_callback(self, post_type):
        def callback(data, response, session):
            posts = self.xreadposts(data, post_type)
            self.extend(posts)
        return callback

    def _generate_populators(self, executor, token, permissions):
        session = requests_futures.sessions.FuturesSession(executor=executor)
        session.mount(GRAPH_ENDPOINT, requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES))

        for offset in xrange(0, NUM_POSTS, CHUNK_SIZE):
            if Permissions.USER_STATUS in permissions:
                yield get_graph_future(session, token, 'me', 'statuses',
                                       offset=offset,
                                       limit=CHUNK_SIZE,
                                       callback=self._make_response_callback('stat'))

                yield get_graph_future(session, token, 'me', 'links',
                                       offset=offset,
                                       limit=CHUNK_SIZE,
                                       callback=self._make_response_callback('link'))

            if Permissions.USER_PHOTOS in permissions:
                yield get_graph_future(session, token, 'me', 'photos',
                                       offset=offset,
                                       limit=CHUNK_SIZE,
                                       callback=self._make_response_callback('photo'))

                yield get_graph_future(session, token, 'me', 'photos', 'uploaded',
                                       offset=offset,
                                       limit=CHUNK_SIZE,
                                       callback=self._make_response_callback('photo_upload'))

            if Permissions.USER_VIDEOS in permissions:
                yield get_graph_future(session, token, 'me', 'videos',
                                       offset=offset,
                                       limit=CHUNK_SIZE,
                                       callback=self._make_response_callback('video'))

                yield get_graph_future(session, token, 'me', 'videos', 'uploaded',
                                       offset=offset,
                                       limit=CHUNK_SIZE,
                                       callback=self._make_response_callback('video_upload'))

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

    def get_aggregate(self):
        aggregates = {}
        seen_posts = set()

        for post in self:
            if post.post_id in seen_posts:
                continue

            seen_posts.add(post.post_id)
            for interaction in post.interactions:
                try:
                    user_aggregate = aggregates[interaction.user_id]
                except KeyError:
                    user_aggregate = UserAggregate(interaction.user_id, interaction.name)
                    aggregates[interaction.user_id] = user_aggregate

                user_aggregate.increment(interaction.type)

        return aggregates

    def get_friend_edges(self):
        network = datastructs.IncomingEdges(self.user)
        for (fbid, user_aggregate) in self.get_aggregate().iteritems():
            friend = datastructs.User(fbid=fbid, name=user_aggregate.name)
            if friend.fbid == self.user.fbid:
                continue

            user_interactions = {
                interaction: user_aggregate.types[interaction]
                for interaction in network.Edge.INTERACTIONS
            }
            network.append(
                network.Edge(
                    target=self.user,
                    source=friend,
                    **user_interactions
                )
            )

        return network
