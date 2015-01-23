from targetshare.models import dynamo, datastructs
from requests.adapters import HTTPAdapter
from collections import defaultdict, namedtuple
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from django.conf import settings
from contextlib import closing
from requests_futures.sessions import FuturesSession
import urllib
import urllib2
import urlparse
LOG = logging.getLogger(__name__)

THREAD_COUNT = 6
NUM_POSTS = 100
CHUNK_SIZE = 20
MAX_TIME_TO_WAIT = 15

STATUS_PERM = 'user_status'
PHOTOS_PERM = 'user_photos'
VIDEOS_PERM = 'user_videos'

USER_NETWORK_CLASS = datastructs.UserNetworkV2

DEFAULT_REQUESTED_PERMISSIONS = set([
    'public_profile',
    'user_friends',
    'email',
    'user_activities',
    'user_birthday',
    'user_location',
    'user_interests',
    'user_likes',
    'user_photos',
    'user_relationships',
    'user_status',
    'user_videos'
])

def process_statuses(session, response, user_id):
    response.data = process_posts(response, 'stat', user_id)


def process_photos(session, response, user_id):
    response.data = process_posts(response, 'photo', user_id)


def process_videos(session, response, user_id):
    response.data = process_posts(response, 'video', user_id)


def process_photo_uploads(session, response, user_id):
    response.data = process_posts(response, 'photo_upload', user_id)


def process_video_uploads(session, response, user_id):
    response.data = process_posts(response, 'video_upload', user_id)


def process_links(session, response, user_id):
    response.data = process_posts(response, 'link', user_id)


def process_posts(response, post_type, user_id):
    stream = Stream(user_id)
    response_data = response.json()
    if 'data' in response_data:
        for post_json in response_data['data']:
            post = Stream.Post(
                post_id=post_json['id'],
                message=post_json.get('message', ""),
                interactions=[]
            )

            if (
                'from' in post_json and
                (post_type == 'photo' or post_type == 'video')
            ):
                user = post_json['from']
                action_type = '{}s_target'.format(post_type)
                post.interactions.append(Stream.Interaction(
                    user['id'],
                    user['name'],
                    action_type
                ))
            if 'tags' in post_json and 'data' in post_json['tags']:
                for user in post_json['tags']['data']:
                    if 'id' not in user:
                        continue
                    action_type = post_type + '_tags'
                    post.interactions.append(Stream.Interaction(
                        user['id'],
                        user['name'],
                        action_type
                    ))
                    if 'place' in post_json:
                        post.interactions.append(Stream.Interaction(
                            user['id'],
                            user['name'],
                            'place_tags',
                        ))
            if 'likes' in post_json and 'data' in post_json['likes']:
                for user in post_json['likes']['data']:
                    action_type = post_type + '_likes'
                    post.interactions.append(Stream.Interaction(
                        user['id'],
                        user['name'],
                        action_type
                    ))
            if 'comments' in post_json and 'data' in post_json['comments']:
                for comment in post_json['comments']['data']:
                    user = comment['from']
                    action_type = post_type + '_comms'
                    post.interactions.append(Stream.Interaction(
                        user['id'],
                        user['name'],
                        action_type
                    ))
            stream.append(post)
    return stream


class StreamAggregate(defaultdict):
    """Stream data aggregator"""
    UserInteractions = namedtuple(
        'UserInteractions',
        ('posts', 'types', 'names')
    )

    def __init__(self, stream):
        super(StreamAggregate, self).__init__(
            lambda: self.UserInteractions(
                posts=defaultdict(lambda: defaultdict(list)),
                types=defaultdict(list),
                names=defaultdict(str),
            )
        )
        seen_posts = set()
        for post in stream:
            if post.post_id in seen_posts:
                continue
            seen_posts.add(post.post_id)
            for interaction in post.interactions:
                # Collect user interactions
                user_interactions = self[interaction.user_id]
                # indexed by user ID & interaction type:
                user_interactions.types[interaction.type].append(interaction)
                # and by user ID, post ID and interaction type:
                user_interactions.posts[post.post_id][interaction.type].\
                    append(interaction)
                if interaction.user_id not in user_interactions.names:
                    user_interactions.names[interaction.user_id] = interaction.name

def queue_job(session, user_id, endpoint, callback, payload):
    return session.get(
        'https://graph.facebook.com/v2.2/{}/{}'.format(user_id, endpoint),
        background_callback=lambda ses, res: callback(ses, res, user_id),
        params=payload,
    )


class Stream(list):
    REPR_OUTPUT_SIZE = 5

    Post = namedtuple('Post', ('post_id', 'message', 'interactions'))
    Interaction = namedtuple('Interaction', ('user_id', 'name', 'type'))

    def __init__(self, user_id, iterable=()):
        super(Stream, self).__init__(iterable)
        self.user_id = user_id

    def __iadd__(self, other):
        if self.user_id != other.user_id:
            raise ValueError("Streams belong to different users")
        self.extend(other)
        return self

    def __add__(self, other):
        new = type(self)(self.user_id, self)
        new += other
        return new

    def __repr__(self):
        data = list(self[:self.REPR_OUTPUT_SIZE + 1])
        if len(data) > self.REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return "{}({!r}, {!r})".format(self.__class__.__name__,
                                       self.user_id,
                                       data)

    def aggregate(self):
        return StreamAggregate(self)

    @classmethod
    def read(cls, user_id, token, permissions=None):
        permissions = permissions or DEFAULT_REQUESTED_PERMISSIONS

        status_authed = STATUS_PERM in permissions
        photos_authed = PHOTOS_PERM in permissions
        videos_authed = VIDEOS_PERM in permissions
        num_posts = NUM_POSTS
        chunk_size = CHUNK_SIZE
        chunk_inputs = []

        # load the queue
        for offset in xrange(0, num_posts, chunk_size):
            chunk_inputs.append((offset, chunk_size))

        stream = cls(user_id)
        with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
            session = FuturesSession(
                executor=executor,
            )
            session.mount('https://', HTTPAdapter(max_retries=3))
            unfinished = []
            for offset, limit in chunk_inputs:
                payload = {
                    'access_token': token,
                    'method': 'GET',
                    'format': 'json',
                    'suppress_http_code': 1,
                    'offset': offset,
                    'limit': limit,
                }
                if status_authed:
                    unfinished.append(queue_job(
                        session,
                        user_id,
                        'statuses',
                        process_statuses,
                        payload
                    ))
                    unfinished.append(queue_job(
                        session,
                        user_id,
                        'links',
                        process_links,
                        payload
                    ))
                if photos_authed:
                    unfinished.append(queue_job(
                        session,
                        user_id,
                        'photos',
                        process_photos,
                        payload
                    ))
                    unfinished.append(queue_job(
                        session,
                        user_id,
                        'photos/uploaded',
                        process_photo_uploads,
                        payload
                    ))
                if videos_authed:
                    unfinished.append(queue_job(
                        session,
                        user_id,
                        'videos',
                        process_videos,
                        payload
                    ))
                    unfinished.append(queue_job(
                        session,
                        user_id,
                        'videos/uploaded',
                        process_video_uploads,
                        payload
                    ))
            try:
                for done_future in as_completed(unfinished, MAX_TIME_TO_WAIT):
                    exc = done_future.exception()
                    if exc:
                        LOG.warning(
                            "Error opening retrieving Facebook data %r",
                            getattr(exc, 'reason', ''),
                            exc_info=True
                        )
                    else:
                        stream += done_future.result().data

            except TimeoutError as exc:
                LOG.warning(
                    "Could not finish retrieving Facebook data in time: %r",
                    getattr(exc, 'reason', ''),
                    exc_info=True
                )

        return stream

    def get_friend_edges(self):
        friend_streamrank = self.aggregate()

        interaction_types = datastructs.INTERACTION_TYPES
        network = USER_NETWORK_CLASS()
        for fbid, user_aggregate in friend_streamrank.iteritems():
            # TODO: figure out if we want to do this here, or filter it out later
            if str(fbid) == str(self.user_id):
                continue
            user_interactions = user_aggregate.types
            incoming = dynamo.IncomingEdge(
                fbid_target=self.user_id,
                fbid_source=fbid,
                **{typ: len(user_interactions[typ]) for typ in interaction_types}
            )
            prim = dynamo.User(fbid=self.user_id)
            user = dynamo.User(fbid=fbid, fullname=user_aggregate.names[fbid])

            interactions = {
                dynamo.PostInteractions(
                    user=user,
                    postid=post_id,
                    **{typ: len(post_interactions[typ]) for typ in interaction_types}
                )
                for (post_id, post_interactions) in user_aggregate.posts.iteritems()
            }

            network.append(
                network.Edge(
                    primary=prim,
                    secondary=user,
                    incoming=incoming,
                    interactions=interactions,
                )
            )

        return network


def urlload(url, query=(), timeout=None):
    """Load data from the given Facebook URL."""
    parsed_url = urlparse.urlparse(url)
    query_params = urlparse.parse_qsl(parsed_url.query)
    query_params.extend(getattr(query, 'items', lambda: query)())
    url = parsed_url._replace(query=urllib.urlencode(query_params)).geturl()

    with closing(urllib2.urlopen(
        url, timeout=(timeout or settings.FACEBOOK.api_timeout))
    ) as response:
        return json.load(response)
