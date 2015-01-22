from targetshare.models import dynamo, datastructs
from django.core.management.base import NoArgsCommand
from collections import defaultdict, namedtuple
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from contextlib import closing
import time
from requests_futures.sessions import FuturesSession
import urllib
import urllib2
import threading
import urlparse
LOG = logging.getLogger(__name__)

TOKEN = 'CAACEdEose0cBAG1j7ZCo2JUSMgRCZAxpzSQpSZBM7JXKFXo1KpyYsQDKApV33kxy7W3weSgxOJKuuFYVXNcTUZCtRsVZCCaxPYGEQd6d29GL863FqMEYdZBcvW5RSN08ME8ZCv3ZBjWvYKJJaByxMyvrqdrCU80xhl435OX1rJcGHpIVhBFZAZCfj4Ao7gNroeq2kdYDws9dVrnKtbQLdrfPtZCY1NW4kCEqhMZD'
USERID = 10102136605223030
#USERID = 2904423

DB_TEXT_LEN = 4096
POSTS_TABLE = 'posts'
USER_POSTS_TABLE = 'user_posts'
LIKES_TABLE = 'page_likes'
USERS_TABLE = 'users'
EDGES_TABLE = 'edges'
LOCALES_TABLE = 'locales'

DEFAULT_DELIMITER = "\t"
POSTS = 'posts'
LINKS = 'links'
LIKES = 'likes'
USERS = 'users'
EDGES = 'edges'
LOCALES = 'locales'
ENTITIES = (POSTS, LINKS, LIKES, USERS, EDGES, LOCALES)

STREAM_DAYS = 365
STREAM_CHUNK_SIZE = 31
THREAD_COUNT = 6
STREAM_READ_TIMEOUT_IN = 5
STREAM_READ_SLEEP_IN = 5
BAD_CHUNK_THRESH = 1
NUM_POSTS = 100

STATUS_AUTHED = True
PHOTOS_AUTHED = True
VIDEOS_AUTHED = True

RANK_WEIGHTS = {
    'photo_tags': 4,
    'photo_likes': 1,
    'photo_comms': 3,
    'photos_target': 2,
    'uplo_tags': 4,
    'uplo_likes': 2,
    'uplo_comms': 4,
    'stat_tags': 4,
    'stat_likes': 2,
    'stat_comms': 4,
}

names = {}

def cb(sess, resp, endpoint):
    #print sess
    #print resp
    #print endpoint
    resp.data = process_posts(resp.json())

def process_posts(d):
    posts = []
    if 'data' in d:
        for post_json in d['data']:
            post = Post(
                post_id=post_json['id'],
                message=post_json.get('message', ""),
                interactions=[]
            )

            if 'icon' in post_json:
                if post_json['from']['id'] == USERID:
                    post_type = 'uplo'
                else:
                    post_type = 'photo'
            else:
                post_type = 'stat'

            if 'from' in post_json and post_type == 'photo':
                user = post_json['from']
                action_type = 'photos_target'
                post.interactions.append(Interaction(user['id'], action_type, RANK_WEIGHTS[action_type]))
                names[user['id']] = user['name']
            if 'tags' in post_json and 'data' in post_json['tags']:
                for user in post_json['tags']['data']:
                    if 'id' not in user:
                        continue
                    action_type = post_type + '_tags'
                    post.interactions.append(Interaction(user['id'], action_type, RANK_WEIGHTS[action_type]))
                    names[user['id']] = user['name']
            if 'likes' in post_json and 'data' in post_json['likes']:
                for user in post_json['likes']['data']:
                    action_type = post_type + '_likes'
                    post.interactions.append(Interaction(user['id'], action_type, RANK_WEIGHTS[action_type]))
                    names[user['id']] = user['name']
            if 'comments' in post_json and 'data' in post_json['comments']:
                for comment in post_json['comments']['data']:
                    user = comment['from']
                    action_type = post_type + '_comms'
                    post.interactions.append(Interaction(user['id'], action_type, RANK_WEIGHTS[action_type]))
                    names[user['id']] = user['name']
            posts.append(post)
    return posts



FBResult = namedtuple("FBResult", "data")

class StreamReaderThread(threading.Thread):
    """Read a chunk of a user's Stream in a thread"""
    def __init__(self, name, user_id, token, results, min_posts, endpoint):
        threading.Thread.__init__(self)
        self.name = name
        self.user_id = user_id
        self.token = token
        self.results = results
        self.min_posts = min_posts
        self.endpoint = endpoint

    def run(self):
        payload = {
            'access_token': self.token,
            'method': 'GET',
            'format': 'json',
            'suppress_http_code': 1,
        }
        url = 'https://graph.facebook.com/v2.2/{}/{}/'.format(self.user_id, self.endpoint)
        timeout = 5
        data = []
        while url and len(data) < self.min_posts:
            paginated_data = urlload(
                url, payload, timeout=timeout)
            url = None
            if paginated_data.get('data'):
                data.extend(process_posts(paginated_data))
                url = paginated_data.get('paging', {}).get('next')
        self.results.append(FBResult(data))


def run_thread_paginate():
    min_posts = NUM_POSTS
    user_id = USERID
    token = TOKEN
    endpoints = []
    if STATUS_AUTHED:
        endpoints.append('statuses')
        endpoints.append('links')
    if PHOTOS_AUTHED:
        endpoints.append('photos')
        endpoints.append('photos/uploaded')
    if VIDEOS_AUTHED:
        endpoints.append('videos')
        endpoints.append('videos/uploaded')
    threads = []
    chunk_outputs = []
    for endpoint in endpoints:
        thread = StreamReaderThread(
            "%s-%s" % (user_id, endpoint),
            user_id,
            token,
            chunk_outputs,
            min_posts,
            endpoint,
        )
        thread.setDaemon(True)
        thread.start()
        threads.append(thread)
    time_stop = time.time() + 20
    while time.time() < time_stop:
        if any(thread.isAlive() for thread in threads):
            time.sleep(1)
        else:
            break

    process(chunk_outputs)

class StreamAggregate(defaultdict):
    """Stream data aggregator"""
    UserInteractions = namedtuple('UserInteractions', ('posts', 'types', 'names'))

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
            #print post
            if post.post_id in seen_posts:
                #print "skipping", post.post_id
                continue
            seen_posts.add(post.post_id)
            for interaction in post.interactions:
                # Collect user interactions
                user_interactions = self[interaction.user_id]
                # indexed by user ID & interaction type:
                user_interactions.types[interaction.type].append(interaction)
                # and by user ID, post ID and interaction type:
                user_interactions.posts[post.post_id][interaction.type].append(interaction)

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
        return {fbid: position for (position, fbid) in enumerate(ranked_friends)}


Post = namedtuple('Post', ('post_id', 'message', 'interactions'))
Interaction = namedtuple('Interaction', ('user_id', 'type', 'weight'))

def run_offsetpartitioned():
    user_id = USERID
    token = TOKEN
    num_posts = NUM_POSTS
    chunk_size = 20
    chunk_inputs = []
    chunk_outputs = [] # list of stream obects holding results

    # load the queue
    for offset in xrange(0, num_posts, chunk_size):
        chunk_inputs.append((offset, chunk_size))

    session = FuturesSession(executor=ThreadPoolExecutor(max_workers=THREAD_COUNT))
    futures = []
    for offset, limit in chunk_inputs:
        payload = {
            'access_token': token,
            'method': 'GET',
            'format': 'json',
            'suppress_http_code': 1,
            'offset': offset,
            'limit': limit,
        }
        if STATUS_AUTHED:
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/statuses/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'statuses'),
                params=payload,
            ))
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/links/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'links'),
                params=payload,
            ))
        if PHOTOS_AUTHED:
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/photos/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'photos_of_me'),
                params=payload,
            ))
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/photos/uploaded/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'photos_i_uploaded'),
                params=payload,
            ))
        if VIDEOS_AUTHED:
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/videos/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'videos_of_me'),
                params=payload,
            ))
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/videos/uploaded/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'videos_i_uploaded'),
                params=payload,
            ))
    for future in futures:
        chunk_outputs.append(future.result())

    process(chunk_outputs)

def run_timepartitioned():
    user_id = USERID
    token = TOKEN
    num_days = STREAM_DAYS
    chunk_size = STREAM_CHUNK_SIZE
    min_posts = NUM_POSTS
    chunk_inputs = []
    #chunk_inputs = Queue.Queue() # fill with (time0, time1) pairs
    chunk_outputs = [] # list of stream obects holding results

    # load the queue
    chunk_size_secs = chunk_size * 24 * 60 * 60
    time_now = int(time.time())
    time_start = time_now - num_days * 24 * 60 * 60
    for time0 in xrange(time_start, time_now, chunk_size_secs):
        time1 = min(time0 + chunk_size_secs, time_now)
        chunk_inputs.append((time0, time1))
        #chunk_inputs.put((time0, time1, 0))

    session = FuturesSession(executor=ThreadPoolExecutor(max_workers=THREAD_COUNT))
    futures = []
    for min_time, max_time in chunk_inputs:
        payload = {
            'access_token': token,
            'method': 'GET',
            'format': 'json',
            'suppress_http_code': 1,
            'since': min_time,
            'limit': 5000,
            'until': max_time,
        }
        if STATUS_AUTHED:
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/statuses/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'statuses'),
                params=payload,
            ))
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/links/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'links'),
                params=payload,
            ))
        if PHOTOS_AUTHED:
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/photos/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'photos_of_me'),
                params=payload,
            ))
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/photos/uploaded/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'photos_i_uploaded'),
                params=payload,
            ))
        if VIDEOS_AUTHED:
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/videos/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'videos_of_me'),
                params=payload,
            ))
            futures.append(session.get(
                'https://graph.facebook.com/v2.2/{}/videos/uploaded/'.format(user_id),
                background_callback=lambda sess, resp: cb(sess, resp, 'videos_i_uploaded'),
                params=payload,
            ))

    for future in futures:
        chunk_outputs.append(future.result())

    process(chunk_outputs)

def process(chunk_outputs):
    total_stream = [item for sublist in chunk_outputs for item in sublist.data]
    friend_streamrank = StreamAggregate(total_stream)

    network = datastructs.UserNetworkV2()
    for fbid, user_aggregate in friend_streamrank.iteritems():
        user_interactions = user_aggregate.types
        #print fbid, names[fbid], user_interactions
        incoming = dynamo.IncomingEdge(
            fbid_target=USERID,
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

    edges_ranked = network.ranked(
        require_incoming=True,
        require_outgoing=False,
    )
    for e in edges_ranked[:10]:
        print e.secondary, names[unicode(e.secondary.fbid)], e.px4_score, len(e.interactions)

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

class Command(NoArgsCommand):
    help = "Test"

    def handle_noargs(self, *args, **options):
        print "threads?"
        start = time.time()
        run_thread_paginate()
        end = time.time()
        print "ran in", end - start

        print "offset?"
        start = time.time()
        run_offsetpartitioned()
        end = time.time()
        print "ran in", end - start

        print "time?"
        start = time.time()
        run_timepartitioned()
        end = time.time()
        print "ran in", end - start
