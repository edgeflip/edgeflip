from targetshare.models import dynamo, datastructs
from collections import defaultdict, namedtuple
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from itertools import tee, filterfalse
import time
from contextlib import closing
from requests_futures.sessions import FuturesSession
import urllib
import urllib2
import urlparse
LOG = logging.getLogger(__name__)

STREAM_DAYS = 365
STREAM_CHUNK_SIZE = 31
THREAD_COUNT = 6
STREAM_READ_TIMEOUT_IN = 5
STREAM_READ_SLEEP_IN = 5
BAD_CHUNK_THRESH = 1
NUM_POSTS = 100
MAX_TIME_TO_WAIT = 15

STATUS_PERM = 'user_status'
PHOTOS_PERM = 'user_photos'
VIDEOS_PERM = 'user_videos'

RANK_WEIGHTS = {
    'media_tags': 4,
    'media_likes': 1,
    'media_comms': 3,
    'media_targets': 2,
    'uplo_tags': 4,
    'uplo_likes': 2,
    'uplo_comms': 4,
    'stat_tags': 4,
    'stat_likes': 2,
    'stat_comms': 4,
}

names = {}


def process_statuses(session, response, user_id):
    response.data = process_posts(response, 'stat', user_id)


def process_photos(session, response, user_id):
    response.data = process_posts(response, 'media', user_id)


def process_videos(session, response, user_id):
    response.data = process_posts(response, 'media', user_id)


def process_photo_uploads(session, response, user_id):
    response.data = process_posts(response, 'uplo', user_id)


def process_video_uploads(session, response, user_id):
    response.data = process_posts(response, 'uplo', user_id)


def process_links(session, response, user_id):
    response.data = process_posts(response, 'post', user_id)


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

            if 'from' in post_json and post_type == 'media':
                user = post_json['from']
                action_type = 'media_target'
                post.interactions.append(Stream.Interaction(
                    user['id'],
                    action_type,
                    RANK_WEIGHTS[action_type])
                )
                names[user['id']] = user['name']
            if 'tags' in post_json and 'data' in post_json['tags']:
                for user in post_json['tags']['data']:
                    if 'id' not in user:
                        continue
                    action_type = post_type + '_tags'
                    post.interactions.append(Stream.Interaction(
                        user['id'],
                        action_type,
                        RANK_WEIGHTS[action_type])
                    )
                    names[user['id']] = user['name']
            if 'likes' in post_json and 'data' in post_json['likes']:
                for user in post_json['likes']['data']:
                    action_type = post_type + '_likes'
                    post.interactions.append(Stream.Interaction(
                        user['id'],
                        action_type,
                        RANK_WEIGHTS[action_type])
                    )
                    names[user['id']] = user['name']
            if 'comments' in post_json and 'data' in post_json['comments']:
                for comment in post_json['comments']['data']:
                    user = comment['from']
                    action_type = post_type + '_comms'
                    post.interactions.append(Stream.Interaction(
                        user['id'],
                        action_type,
                        RANK_WEIGHTS[action_type])
                    )
                    names[user['id']] = user['name']
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

    def ranking(self):
        """Reduce the aggregate to a mapping of friends and their normalized
        rankings.

        """
        friend_total = defaultdict(int)
        for user_id, user_interactions in self.iteritems():
            for interactions in user_interactions.types.itervalues():
                for interaction in interactions:
                    friend_total[user_id] += interaction.weight

        ranked_friends = sorted(friend_total,
                                key=lambda user_id: friend_total[user_id],
                                reverse=True)
        return {fbid: pos for (pos, fbid) in enumerate(ranked_friends)}


def partition(pred, iterable):
    'Use a predicate to partition entries into false entries and true entries'
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)


def queue_job(session, user_id, endpoint, callback, payload):
    return session.get(
        'https://graph.facebook.com/v2.2/{}/{}'.format(user_id, endpoint),
        background_callback=lambda ses, res: callback(ses, res, user_id),
        params=payload,
    )


class Stream(list):
    REPR_OUTPUT_SIZE = 5

    Post = namedtuple('Post', ('post_id', 'message', 'interactions'))
    Interaction = namedtuple('Interaction', ('user_id', 'type', 'weight'))

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
                                       self.user.fbid,
                                       data)

    def aggregate(self):
        return self.StreamAggregate(self)

    @classmethod
    def read(cls, user, token):
        permissions = set(['public_profile', 'user_friends', 'email', 'user_activities', 'user_birthday', 'user_location', 'user_interests', 'user_likes', 'user_photos', 'user_relationships', 'user_status', 'user_videos'])

        status_authed = STATUS_PERM in permissions
        photos_authed = PHOTOS_PERM in permissions
        videos_authed = VIDEOS_PERM in permissions
        user_id = user.asid
        num_posts = NUM_POSTS
        chunk_size = 20
        chunk_inputs = []

        # load the queue
        for offset in xrange(0, num_posts, chunk_size):
            chunk_inputs.append((offset, chunk_size))

        session = FuturesSession(
            executor=ThreadPoolExecutor(max_workers=THREAD_COUNT)
        )
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
        start = time.time()
        last_call = start + MAX_TIME_TO_WAIT
        stream = cls(user)
        while len(unfinished) > 0 and time.time() < last_call:
            done_futures, unfinished = partition(lambda x: x.done(), unfinished)
            print "done =", len(done_futures), "not done =", len(unfinished)
            for done_future in done_futures:
                stream += done_future.result()
            time.sleep(1)

        return stream


    def get_friend_edges(self):
        friend_streamrank = StreamAggregate(stream)

        network = datastructs.UserNetwork()
        for fbid, user_aggregate in friend_streamrank.iteritems():
            user_interactions = user_aggregate.types
            incoming = dynamo.IncomingEdge(
                fbid_target=self.user_id,
                fbid_source=fbid,
                stat_likes=len(user_interactions['stat_likes']),
                stat_comms=len(user_interactions['stat_comms']),
                stat_tags=len(user_interactions['stat_tags']),
                photo_tags=len(user_interactions['photo_tags']),
                photo_likes=len(user_interactions['photo_likes']),
                photo_comms=len(user_interactions['photo_comms']),
                photos_target=len(user_interactions['photos_target']),
                uplo_likes=len(user_interactions['uplo_likes']),
                uplo_comms=len(user_interactions['uplo_comms']),
            )
            prim = dynamo.User(fbid=USERID)
            user = dynamo.User(fbid=fbid)

            interactions = {
                dynamo.PostInteractions(
                    user=user,
                    postid=post_id,
                    stat_likes=len(post_interactions['stat_likes']),
                    stat_comms=len(post_interactions['stat_comms']),
                    stat_tags=len(post_interactions['stat_tags']),
                    photo_tags=len(post_interactions['photo_tags']),
                    photo_likes=len(post_interactions['photo_likes']),
                    photo_comms=len(post_interactions['photo_comms']),
                    photos_target=len(post_interactions['photos_target']),
                    uplo_likes=len(post_interactions['uplo_likes']),
                    uplo_comms=len(post_interactions['uplo_comms']),
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


def get_user(uid, token):
    """Retrieve primary user data from Facebook.

    Returns a User.

    """
    return dynamo.User(
        asid=uid,
        #TODO: get other data from appropriate endpoints
    )


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
