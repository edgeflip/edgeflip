from targetshare.integration import facebook
from targetshare.models import dynamo, datastructs
from targetshare import utils
from django.utils import timezone
from django.core.management.base import NoArgsCommand
from faraday.utils import epoch
from collections import defaultdict, namedtuple
from urlparse import urlparse
from cStringIO import StringIO
import datetime
import unicodecsv
import itertools
import logging
from concurrent.futures import ThreadPoolExecutor
import time
from requests_futures.sessions import FuturesSession
LOG = logging.getLogger(__name__)

TOKEN = ''

USERID = 10102136605223030
#USERID = 751

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

STREAM_DAYS = 120
STREAM_CHUNK_SIZE = 10
THREAD_COUNT = 6
STREAM_READ_TIMEOUT_IN = 5
STREAM_READ_SLEEP_IN = 5
BAD_CHUNK_THRESH = 1


def retrieve_fb_feed(app_scoped_id, token, until):
    ''' Seeds to FeedKey.data element from FB '''
    return facebook.client.urlload(
        'https://graph.facebook.com/v2.2/{}/feed/'.format(app_scoped_id), {
            'access_token': token,
            'method': 'GET',
            'format': 'json',
            'suppress_http_code': 1,
            'limit': 5000,
            'until': until,
        }, timeout=120
    )


def crawl(user_id, token):
    now_epoch = epoch.from_date(timezone.now())
    ts = now_epoch
    data = retrieve_fb_feed(user_id, token, ts)
    print data
    yield data
    next_url = data.get('paging', {}).get('next')
    while next_url and 'data' in data:
        try:
            print "getting ", next_url
            data = facebook.client.urlload(next_url)
        except (ValueError, IOError):
            print "retrying"
            next
        yield data
        next_url = data.get('paging', {}).get('next')

# Despite what the docs say, datetime.strptime() format doesn't like %z
# see: http://stackoverflow.com/questions/526406/python-time-to-age-part-2-timezones/526450#526450
def parse_ts(time_string):
    tz_offset_hours = int(time_string[-5:]) / 100  # we're ignoring the possibility of minutes here
    tz_delt = datetime.timedelta(hours=tz_offset_hours)
    return datetime.datetime.strptime(time_string[:-5], "%Y-%m-%dT%H:%M:%S") - tz_delt


class FeedPostFromJson(object):
    """Each post contributes a single post line, and multiple user-post lines to the db"""

    def __init__(self, post_json):
        self.post_id = str(post_json['id'])
        # self.post_ts = post_json['updated_time']
        self.post_ts = parse_ts(post_json['updated_time'])
        self.post_type = post_json['type']
        self.post_app = post_json['application']['id'] if 'application' in post_json else ""
        self.post_app_name = post_json['application']['name'] if 'application' in post_json else ""
        self.post_from = post_json['from']['id'] if 'from' in post_json else ""
        self.post_link = post_json.get('link', "")
        try:
            self.post_link_domain = urlparse(self.post_link).hostname if (self.post_link) else ""
        except ValueError: # handling invalid Ipv6 address errors
            self.post_link_domain = ""

        self.post_story = post_json.get('story', "")
        self.post_description = post_json.get('description', "")
        self.post_caption = post_json.get('caption', "")
        self.post_message = post_json.get('message', "")
        self.post_storytags = post_json.get('story_tags', {})
        self.post_status_type = post_json.get('status_type', "")
        self.post_likes = post_json.get('likes', [])
        self.post_comments = post_json.get('comments', [])
        self.post_shares = post_json.get('to', [])
        self.post_place = post_json.get('place', {})
        self.post_withtags = post_json.get('with_tags', [])

        if 'to' in post_json and 'data' in post_json['to']:
            self.to_ids = set()
            self.to_ids.update([user['id'] for user in post_json['to']['data']])
        if 'likes' in post_json and 'data' in post_json['likes']:
            self.like_ids = set()
            self.like_ids.update([user['id'] for user in post_json['likes']['data']])
        if 'comments' in post_json and 'data' in post_json['comments']:
            self.comments = [{
                'comment_id': comment['id'],
                'commenter_id': comment['from']['id'],
                'message': comment['message']
            } for comment in post_json['comments']['data']]
            self.commenters = defaultdict(list)
            for comment in self.comments:
                self.commenters[comment['commenter_id']].append(comment['message'])

class Feed(object):
    """Holds an entire feed from a single user crawl"""

    def __init__(self, user_id):
        self.initialize(user_id)

    def initialize(self, user_id):
        self.output_formatter = {
            POSTS: self.post_lines,
            LINKS: self.link_lines,
            LIKES: self.like_lines,
            USERS: self.user_lines,
            EDGES: self.edge_lines,
            LOCALES: self.locale_lines,
        }
        self.user_id = user_id
        self.posts = []
        self.counts = dict()
        self.strings = dict()
        self.writers = dict()
        for entity in ENTITIES:
            self.counts[entity] = 0
            self.strings[entity] = StringIO()
            self.writers[entity] = unicodecsv.writer(
                self.strings[entity],
                encoding='utf-8',
                delimiter="\t"
            )

    def add_post(self, post):
        self.posts.append(post)

    def write(self):
        for entity in ENTITIES:
            lines = self.get_output_lines(entity)
            for line in lines:
                self.writers[entity].writerow(line)
            self.counts[entity] += len(lines)
            print self.strings[entity]
            with open(entity, 'a') as f:
                f.write(self.strings[entity].getvalue())


    def transform_field(self, field, delim):
        if isinstance(field, basestring):
            return field.replace(delim, " ").replace("\n", " ").replace("\x00", "").encode('utf8', 'ignore')
        else:
            return str(field)

    @property
    def post_corpus(self):
        corpus = ""
        for post in self.posts:
            corpus += post.post_message + " "
        return corpus

    def post_lines(self, delim):
        post_lines = []
        for post in self.posts:
            post_fields = (
                self.user_id,
                post.post_id,
                post.post_ts,
                post.post_type,
                post.post_status_type,
                post.post_app,
                post.post_app_name,
                post.post_from,
                post.post_link,
                post.post_link_domain,
                post.post_story,
                post.post_description,
                post.post_caption,
                post.post_message,
                len(post.like_ids) if hasattr(post, 'like_ids') else 0,
                len(post.comments) if hasattr(post, 'comments') else 0,
                len(post.to_ids) if hasattr(post, 'to_ids') else 0,
                len(post.commenters) if hasattr(post, 'commenters') else 0,
            )
            post_lines.append(
                tuple(self.transform_field(field, delim) for field in post_fields)
            )
        return post_lines

    def link_lines(self, delim):
        link_lines = []
        for p in self.posts:
            user_ids = None
            if hasattr(p, 'to_ids'):
                user_ids = p.to_ids
            if hasattr(p, 'like_ids'):
                if user_ids:
                    user_ids = user_ids.union(p.like_ids)
                else:
                    user_ids = p.like_ids
            if hasattr(p, 'commenters'):
                commenter_ids = p.commenters.keys()
                if user_ids:
                    user_ids = user_ids.union(commenter_ids)
                else:
                    user_ids = commenter_ids
            if user_ids:
                for user_id in user_ids:
                    has_to = "1" if hasattr(p, 'to_ids') and user_id in p.to_ids else ""
                    has_like = "1" if hasattr(p, 'like_ids') and user_id in p.like_ids else ""
                    if hasattr(p, 'commenters') and user_id in commenter_ids:
                        has_comm = "1"
                        # we're doing bag of words so separating comments
                        # more granularly than this shouldn't matter
                        comment_text = " ".join(p.commenters[user_id])
                        num_comments = str(len(p.commenters[user_id]))
                    else:
                        has_comm = ""
                        comment_text = ""
                        num_comments = "0"

                    link_fields = (
                        p.post_id,
                        user_id,
                        self.user_id,
                        has_to,
                        has_like,
                        has_comm,
                        num_comments,
                        comment_text
                    )
                    link_lines.append(
                        self.transform_field(f, delim) for f in link_fields
                    )
        return link_lines


    def like_lines(self, delim):
        like_lines = []
        for post in self.posts:
            if post.post_type == 'link':
                if post.post_app == "2530096808" or ' likes ' in post.post_story:
                    for story_tag in post.post_storytags.values():
                        if story_tag[0]['type'] == 'page':
                            like_fields = (
                                self.user_id,
                                story_tag[0]['id'],
                                story_tag[0]['name'],
                                post.post_ts,
                            )
                            like_lines.append(
                                self.transform_field(f, delim) for f in like_fields
                            )
        return like_lines

    def user_lines(self, delim):
        user_lines = []
        users = {}
        for post in self.posts:
            if post.post_status_type == 'approved_friend':
                for story_tag in post.post_storytags.values():
                    if story_tag[0]['type'] == 'user':
                        user_id = story_tag[0]['id']
                        if user_id not in users:
                            users[user_id] = story_tag[0]['name']
        for user_id, name in users.iteritems():
            user_fields = (
                user_id,
                name,
            )
            user_lines.append(
                self.transform_field(f, delim) for f in user_fields
            )
        return user_lines


    def edge_lines(self, delim):
        edges = {}
        for post in self.posts:
            if 'data' in post.post_comments:
                for comment in post.post_comments['data']:
                    secondary = comment['from']['id']
                    if secondary not in edges:
                        edges[secondary] = {
                            'num_comments': 0,
                            'num_likes': 0,
                            'num_shares': 0,
                            'latest_activity': datetime.datetime(datetime.MINYEAR, 1, 1),
                        }
                    edges[secondary]['num_comments'] += 1
                    ts = parse_ts(comment['created_time'])
                    if ts > edges[secondary]['latest_activity']:
                        edges[secondary]['latest_activity'] = ts
            if 'data' in post.post_likes:
                for like in post.post_likes['data']:
                    secondary = like['id']
                    if secondary not in edges:
                        edges[secondary] = {
                            'num_comments': 0,
                            'num_likes': 0,
                            'num_shares': 0,
                            'latest_activity': datetime.datetime(datetime.MINYEAR, 1, 1),
                        }
                    edges[secondary]['num_likes'] += 1
                    if post.post_ts > edges[secondary]['latest_activity']:
                        edges[secondary]['latest_activity'] = post.post_ts
            if 'data' in post.post_shares:
                for share in post.post_shares['data']:
                    secondary = share['id']
                    if secondary not in edges:
                        edges[secondary] = {
                            'num_comments': 0,
                            'num_likes': 0,
                            'num_shares': 0,
                            'latest_activity': datetime.datetime(datetime.MINYEAR, 1, 1),
                        }
                    edges[secondary]['num_shares'] += 1
                    if post.post_ts > edges[secondary]['latest_activity']:
                        edges[secondary]['latest_activity'] = post.post_ts

        edge_lines = []
        for secondary in edges:
            edge_fields = (
                self.user_id,
                secondary,
                edges[secondary]['num_comments'],
                edges[secondary]['num_likes'],
                edges[secondary]['num_shares'],
                edges[secondary]['latest_activity'],
            )
            edge_lines.append(
                self.transform_field(f, delim) for f in edge_fields
            )

        return edge_lines

    def locale_lines(self, delim):
        locale_lines = []
        for post in self.posts:
            if 'location' in post.post_place:
                if isinstance(post.post_place['location'], dict):
                    locale_fields = [
                        post.post_place.get('id', ''),
                        post.post_place.get('name', ''),
                        post.post_place['location'].get('city', ''),
                        post.post_place['location'].get('state', ''),
                        post.post_place['location'].get('zip', ""),
                        post.post_place['location'].get('country', ""),
                        post.post_place['location'].get('street', ""),
                    ]
                else:
                    locale_fields = [
                        post.post_place.get('id', ''),
                        post.post_place.get('name', ''),
                        '',
                        '',
                        '',
                        '',
                        '',
                    ]

                locale_lines.append(
                    self.transform_field(f, delim) for f in locale_fields + [self.user_id]
                )
                if 'data' in post.post_withtags:
                    for tagged in post.post_withtags['data']:
                        locale_lines.append(
                            self.transform_field(f, delim) for f in locale_fields + [tagged['id']]
                        )
        return locale_lines



    def get_output_lines(self, entity, delim=DEFAULT_DELIMITER):
        formatter = self.output_formatter[entity]
        return formatter(delim)

RANK_WEIGHTS = {
    'post_likes': 2,
    'post_comms': 4,
    'stat_likes': 2,
    'stat_comms': 4,
    'wall_posts': 2,
    'wall_comms': 4,
    'tags': 1,
}


def cb(sess, resp):
    d = resp.json()
    posts = []
    if 'data' in d:
        for post_json in d['data']:
            post = Post(
                post_id=post_json['id'],
                message=post_json.get('message', ""),
                interactions=[]
            )
            poster = post_json['from']['id']
            i_am_source = str(poster) == str(USERID)

            post_type = post_json['type']
            if not i_am_source and post_type is not 'status':
                post.interactions.append(Interaction(poster, 'wall_posts', 2))
            if 'to' in post_json and 'data' in post_json['to']:
                for user in post_json['to']['data']:
                    action_type = 'tags'
                    post.interactions.append(Interaction(user['id'], action_type, 1))
            if 'likes' in post_json and 'data' in post_json['likes']:
                for user in post_json['likes']['data']:
                    action_type = 'stat_likes' if post_type == 'status' else 'post_likes'
                    post.interactions.append(Interaction(user['id'], action_type, 2))
            if 'comments' in post_json and 'data' in post_json['comments']:
                for comment in post_json['comments']['data']:
                    if post_type == 'status':
                        action_type = 'stat_comms'
                    elif i_am_source:
                        action_type = 'post_comms'
                    else:
                        action_type = 'wall_comms'

                    post.interactions.append(Interaction(user['id'], action_type, 4))
            posts.append(post)
    resp.data = posts

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
        for post in stream:
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

def read():
    user_id = USERID
    token = TOKEN
    num_days = STREAM_DAYS
    chunk_size = STREAM_CHUNK_SIZE
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
        futures.append(session.get(
            'https://graph.facebook.com/v2.2/{}/feed/'.format(user_id),
            background_callback=cb,
            params=payload,
        ))
    for future in futures:
        chunk_outputs.append(future.result())

    total_stream = [item for sublist in chunk_outputs for item in sublist.data]
    friend_streamrank = StreamAggregate(total_stream)

    network = datastructs.UserNetwork()
    for fbid, user_aggregate in friend_streamrank.iteritems():
        user_interactions = user_aggregate.types
        incoming = dynamo.IncomingEdge(
            fbid_target=USERID,
            fbid_source=fbid,
            post_likes=len(user_interactions['post_likes']),
            post_comms=len(user_interactions['post_comms']),
            stat_likes=len(user_interactions['stat_likes']),
            stat_comms=len(user_interactions['stat_comms']),
            wall_posts=len(user_interactions['wall_posts']),
            wall_comms=len(user_interactions['wall_comms']),
            tags=len(user_interactions['tags']),
        )
        print incoming
        prim = dynamo.User(fbid=USERID)
        user = dynamo.User(fbid=fbid)

        interactions = {
            dynamo.PostInteractions(
                user=user,
                postid=post_id,
                post_likes=len(post_interactions['post_likes']),
                post_comms=len(post_interactions['post_comms']),
                stat_likes=len(post_interactions['stat_likes']),
                stat_comms=len(post_interactions['stat_comms']),
                wall_posts=len(post_interactions['wall_posts']),
                wall_comms=len(post_interactions['wall_comms']),
                tags=len(post_interactions['tags']),
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
    print edges_ranked


class Command(NoArgsCommand):
    help = "Test"

    def handle_noargs(self, *args, **options):
        read()
