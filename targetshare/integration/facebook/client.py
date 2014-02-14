import sys
import time
import datetime
import urllib
import urllib2
import urlparse
import json
import logging
import threading
import Queue
from collections import defaultdict, namedtuple
from contextlib import closing
from math import ceil

import requests

from django.conf import settings
from django.utils import timezone

from targetshare import utils
from targetshare.models import datastructs, dynamo


LOG = logging.getLogger(__name__)


# stock queries for facebook #

class STREAMTYPE:
    """bag of facebook codes"""
    GROUP_CREATED = 11
    EVENT_CREATED = 12
    STATUS_UPDATE = 46
    WALL_POST = 56
    NOTE_CREATED = 66
    LINK = 80
    VIDEO = 128
    PHOTO = 247
    APP_STORY = 237
    COMMENT_CREATED = 257
    APP_STORY2 = 272
    CHECKIN = 285
    GROUP_POST = 308


def fql_stream_chunk(uid, min_time, max_time):
    return ("SELECT created_time, post_id, source_id, target_id, type, actor_id, tagged_ids, message FROM stream "
            "WHERE source_id={} AND {} <= created_time AND created_time < {} LIMIT 5000"
            .format(uid, min_time, max_time))


def fql_post_comms(stream):
    return ("SELECT fromid, post_id FROM comment "
            "WHERE post_id IN ("
                "SELECT post_id FROM {} WHERE type != {}"
            ")"
            .format(stream, STREAMTYPE.STATUS_UPDATE))


def fql_post_likes(stream): # TODO: add object_id/url for like targeting?
    return ("SELECT user_id, post_id FROM like "
            "WHERE post_id IN ("
                "SELECT post_id FROM {} WHERE type != {}"
            ")"
            .format(stream, STREAMTYPE.STATUS_UPDATE))


def fql_stat_comms(stream):
    return ("SELECT fromid, post_id FROM comment "
            "WHERE post_id IN ("
                "SELECT post_id FROM {} WHERE type = {}"
            ")"
            .format(stream, STREAMTYPE.STATUS_UPDATE))


def fql_stat_likes(stream):
    return ("SELECT user_id, post_id FROM like "
            "WHERE post_id IN ("
                "SELECT post_id FROM {} WHERE type = {}"
            ")"
            .format(stream, STREAMTYPE.STATUS_UPDATE))


def fql_wall_posts(stream, uid):
    return ("SELECT actor_id, post_id FROM {} "
            "WHERE type != {} AND actor_id != {}"
            .format(stream, STREAMTYPE.STATUS_UPDATE, uid))


def fql_wall_comms(wall, uid):
    return ("SELECT actor_id, post_id FROM {0} "
            "WHERE post_id IN ("
                "SELECT post_id FROM comment "
                "WHERE post_id IN (SELECT post_id FROM {0}) AND fromid = {1}"
            ")"
            .format(wall, uid))


def fql_tags(stream, uid):
    return ("SELECT tagged_ids, post_id FROM {} "
            "WHERE actor_id = {} AND type != {}"
            .format(stream, uid, STREAMTYPE.PHOTO))

#TODO: perhaps this will tighten these up:
#TODO: http://facebook.stackoverflow.com/questions/10836965/get-posts-made-by-facebook-friends-only-on-page-through-graphapi/10837566#10837566

#TODO: Could probably combine these to get rid of the separate "photo" queries;
#TODO: but then each would contain two nested subqueries. Not sure what's worse with FQL.


def fql_tag_photos(fbid):
    return "SELECT object_id FROM photo_tag WHERE subject = {}".format(fbid)


def fql_prim_photos(photos, fbid):
    return ("SELECT object_id FROM photo WHERE object_id IN "
                "(SELECT object_id FROM {}) AND owner = {}"
            .format(photos, fbid))


def fql_prim_tags(photos, fbid):
    return ("SELECT subject FROM photo_tag WHERE object_id IN "
                "(SELECT object_id FROM {}) AND subject != {}"
            .format(photos, fbid))


def fql_other_photos(photos, fbid):
    return ("SELECT object_id FROM photo WHERE object_id IN "
                "(SELECT object_id FROM {}) AND owner != {}"
            .format(photos, fbid))


def fql_other_tags(photos, fbid):
    return ("SELECT subject FROM photo_tag WHERE object_id IN "
                "(SELECT object_id FROM {}) AND subject != {}"
            .format(photos, fbid))


def fql_user_info(uid):
    return ("SELECT uid, first_name, last_name, "
                "email, sex, birthday_date, current_location "
            "FROM user WHERE uid={}"
            .format(uid))


def fql_friend_info(fields, fbid, limit, offset):
    return ("SELECT {} FROM user WHERE uid IN "
                "(SELECT uid2 FROM friend where uid1 = {} "
                 "ORDER BY uid2 LIMIT {} OFFSET {})"
            .format(fields, fbid, limit, offset))


PX3_FIELDS = {
    'uid', 'first_name', 'last_name', 'sex', 'birthday_date',
    'current_location', 'mutual_friend_count'
}

PX3_EXTENDED_FIELDS = {
    'activities',
    'affiliations',
    'books',
    'devices',
    'friend_request_count',
    'has_timeline',
    'interests',
    'languages',
    'likes_count',
    'movies',
    'music',
    'political',
    'profile_update_time',
    'quotes',
    'relationship_status',
    'religion',
    'sports',
    'tv',
    'wall_count',
    # The fields below we may want to turn on again later
    #'is_app_user',
    #'locale',
    #'notes_count',
    #'online_presence',
    #'status',
    #'subscriber_count',
    #'timezone',
}

FULL_PX3_FIELDS = ','.join(PX3_FIELDS | PX3_EXTENDED_FIELDS)


def decode_date(date):
    if date:
        try:
            month, day, year = map(int, date.split('/'))
        except ValueError:
            pass
        else:
            return timezone.datetime(year, month, day, tzinfo=timezone.utc)

    return None


def urlload(url, query=(), timeout=None):
    """Load data from the given Facebook URL."""
    parsed_url = urlparse.urlparse(url)
    query_params = urlparse.parse_qsl(parsed_url.query)
    query_params.extend(getattr(query, 'items', lambda: query)())
    url = parsed_url._replace(query=urllib.urlencode(query_params)).geturl()

    try:
        with closing(urllib2.urlopen(
                url, timeout=(timeout or settings.FACEBOOK.api_timeout))
        ) as response:
            return json.load(response)
    except IOError as exc:
        exc_type, exc_value, trace = sys.exc_info()
        LOG.warning("Error opening URL %s %r", url, getattr(exc, 'reason', ''), exc_info=True)
        try:
            LOG.warning("Returned error message was: %s", exc.read())
        except Exception:
            pass
        raise exc_type, exc_value, trace


def exhaust_pagination(url, retry_limit=3, sleep_duration=5, timeout=120):
    retry_count = 0
    data = []
    LOG.info('Starting pagination dive with {}'.format(url))
    while url:
        try:
            paginated_data = urlload(
                url, timeout=timeout)
        except (ValueError, IOError):
            LOG.debug('Failed to grab next page of data')
            retry_count += 1
            if retry_count > retry_limit:
                LOG.exception('Giving up on this batch of data')
                break
            else:
                time.sleep(sleep_duration)
                continue
        else:
            url = None
            if paginated_data.get('data'):
                data.extend(paginated_data['data'])
                url = paginated_data.get('paging', {}).get('next')

    return data


def _urlload_thread(url, query=(), results=None):
    """Used to read JSON from Facebook in a thread and append output to a list of results"""
    if not hasattr(results, 'extend'):
        raise TypeError("Argument 'results' required and list expected")

    with utils.Timer() as timer:
        response = urlload(url, query)
        data = response['data']
        results.extend(data)

    LOG.debug('Thread %s read %s records from FB in %s',
              threading.current_thread().name, len(data), timer)
    return len(data)


def extend_token(fbid, appid, token):
    """Extend lifetime of a user token from FB."""
    url = 'https://graph.facebook.com/oauth/access_token?' + urllib.urlencode({
        'grant_type': 'fb_exchange_token',
        'fb_exchange_token': token,
        'client_id': appid,
        'client_secret': settings.FACEBOOK.secrets[str(appid)],
    })
    ts = time.time()

    # Unfortunately, FB doesn't seem to allow returning JSON for new tokens,
    # even if you try passing &format=json in the URL.
    try:
        with closing(urllib2.urlopen(url, timeout=settings.FACEBOOK.api_timeout)) as response:
            params = urlparse.parse_qs(response.read())
        token1 = params['access_token'][0]
        expires = int(params['expires'][0])
        LOG.debug("Extended access token %s expires in %s seconds", token1, expires)
        expires1 = ts + expires
    except (IOError, IndexError, KeyError) as exc:
        if hasattr(exc, 'read'): # built-in hasattr won't overwrite exc_info
            error_response = exc.read()
        else:
            error_response = ''
        LOG.warning(
            "Failed to extend token %s%s",
            token,
            error_response and ': %r' % error_response,
            exc_info=True,
        )
        token1 = token
        expires1 = ts

    return dynamo.Token(
        fbid=fbid,
        appid=appid,
        expires=timezone.make_aware(
            datetime.datetime.utcfromtimestamp(expires1),
            timezone.utc
        ),
        token=token1,
    )


def get_user(uid, token):
    """Retrieve primary user data from Facebook.

    Returns a User.

    """
    fql = fql_user_info(uid)
    response_data = urlload('https://graph.facebook.com/fql',
                            {'q': fql, 'format': 'json', 'access_token': token})
    record = response_data['data'][0]
    location = record.get('current_location') or {}
    return dynamo.User(
        fbid=record['uid'],
        fname=record['first_name'],
        lname=record['last_name'],
        email=record.get('email'),
        gender=record['sex'],
        birthday=decode_date(record['birthday_date']),
        city=location.get('city'),
        state=location.get('state'),
        country=location.get('country'),
    )


def get_friend_count(fbid, token):
    num_friends_response = urlload('https://graph.facebook.com/fql', {
        'q': "SELECT friend_count FROM user WHERE uid = {}".format(fbid),
        'format': 'json',
        'access_token': token,
    })
    return num_friends_response['data'][0]['friend_count']


def get_friend_edges(user, token):
    """Retrieve simple information about a user's network.

    Returns the UserNetwork of Edges between the user and friends.

    (See `Stream.get_friend_edges`.)

    """
    LOG.debug("getting friend edges from FB for %d", user.fbid)
    with utils.Timer() as timer:
        edges = _get_friend_edges_simple(user, token)
        edges.sort(key=lambda edge: edge.incoming.mut_friends, reverse=True)
    LOG.debug("got %d friend edges for %d (%s)", len(edges), user.fbid, timer)
    return edges


def _get_friend_edges_simple(user, token):
    """Retrieve basic info on user's FB friends in a single call."""
    LOG.debug("getting friends for %d", user.fbid)

    timer = utils.Timer()
    loop_timeout = settings.FACEBOOK.friendLoop.timeout
    loop_sleep = settings.FACEBOOK.friendLoop.sleep
    limit = settings.FACEBOOK.friendLoop.fqlLimit

    # Get the number of friends from FB to determine how many chunks to run
    num_friends = get_friend_count(user.fbid, token)
    chunks = int(ceil(float(num_friends) / limit)) + 1 # one extra just to be safe

    # Set up the threads for reading the friend info
    threads = []
    friendChunks = []
    for i in range(chunks):
        offset = limit * i
        t = threading.Thread(target=_urlload_thread, args=(
            'https://graph.facebook.com/fql/',
            {
                'q': fql_friend_info(FULL_PX3_FIELDS, user.fbid, limit, offset),
                'format': 'json',
                'access_token': token,
            },
            friendChunks,
        ))
        t.setDaemon(True)
        t.name = "%s-px3-%d" % (user.fbid, i)
        threads.append(t)
        t.start()

    # Photo stuff should return quickly enough that we can grab it at the same time as getting friend info

    tag_label = 'tag_photos'
    primary_label = 'primary_photos'
    other_label = 'other_photos'
    query = {
        tag_label: fql_tag_photos(user.fbid),
        primary_label: fql_prim_photos('#' + tag_label, user.fbid),
        other_label: fql_other_photos('#' + tag_label, user.fbid),
        'primary_photo_tags': fql_prim_tags('#' + primary_label, user.fbid),
        'other_photo_tags': fql_other_tags('#' + other_label, user.fbid),
    }
    photoResults = []
    photoThread = threading.Thread(target=_urlload_thread, args=(
        'https://graph.facebook.com/fql',
        {
            'q': json.dumps(query, separators=(',', ':')), # compact separators
            'format': 'json',
            'access_token': token,
        },
        photoResults,
    ))
    photoThread.setDaemon(True)
    photoThread.name = "%s-px3-photos" % user.fbid
    threads.append(photoThread)
    photoThread.start()

    # Loop until all the threads are done
    # or we've run out of time waiting
    time_stop = time.time() + loop_timeout
    while time.time() < time_stop:
        threads = [thread for thread in threads if thread.isAlive()]
        if threads:
            time.sleep(loop_sleep)
        else:
            break

    # Read out the photo data
    lab_recs = {}
    for entry in photoResults:
        label = entry['name']
        records = entry['fql_result_set']
        lab_recs[label] = records

    primPhotoCounts = defaultdict(int)
    otherPhotoCounts = defaultdict(int)

    for rec in lab_recs.get('primary_photo_tags', []):
        if rec['subject']:
            primPhotoCounts[int(rec['subject'])] += 1

    for rec in lab_recs.get('other_photo_tags', []):
        if rec['subject']:
            otherPhotoCounts[int(rec['subject'])] += 1

    # Use a dictionary to avoid possible duplicates in cases where pagination
    # changes during the query or other FB barf
    friends = set()
    network = datastructs.UserNetwork()
    for rec in friendChunks:
        try:
            friend_id = int(rec['uid'])
        except TypeError:
            # FB returned some gargbage
            raise BadChunksError(
                "_get_friend_edges_simple failed on bad response: {!r}".format(rec)
            )
        else:
            if friend_id in friends:
                continue

        current_location = rec.get('current_location') or {}
        primary_photo_tags = primPhotoCounts[friend_id]
        other_photo_tags = otherPhotoCounts[friend_id]

        if primary_photo_tags + other_photo_tags > 0:
            LOG.debug("Friend %d has %d primary photo tags and %d other photo tags",
                      friend_id, primary_photo_tags, other_photo_tags)

        friend = dynamo.User(
            fbid=friend_id,
            fname=rec['first_name'],
            lname=rec['last_name'],
            gender=rec['sex'],
            birthday=decode_date(rec['birthday_date']),
            city=current_location.get('city'),
            state=current_location.get('state'),
            country=current_location.get('country'),
            data={key: value for (key, value) in rec.items()
                  if key in PX3_EXTENDED_FIELDS},
        )
        edge_data = dynamo.IncomingEdge(
            fbid_source=friend.fbid,
            fbid_target=user.fbid,
            photos_target=primary_photo_tags,
            photos_other=other_photo_tags,
            mut_friends=rec['mutual_friend_count'],
        )

        friends.add(friend.fbid)
        network.append(network.Edge(user, friend, edge_data))

    LOG.debug("returning %d friends for %d (%s)", len(friends), user.fbid, timer)
    return network


def verify_oauth_code(fb_app_id, code, redirect_uri):
    url_params = {
        'client_id': fb_app_id,
        'redirect_uri': redirect_uri,
        'client_secret': settings.FACEBOOK.secrets[str(fb_app_id)],
        'code': code
    }
    try:
        resp = requests.get(
            'https://graph.facebook.com/oauth/access_token',
            params=url_params
        )
    except requests.exceptions.RequestException:
        token = None
    else:
        token = urlparse.parse_qs(resp.content).get('access_token')

    token = token[0] if token else None
    return token is not None


class Stream(list):
    """User stream list

    Stores stream data in the form:

        [
            Post(post_id=123,
                 message=...,
                 interactions=[
                     Interaction(
                         user_id=098,
                         type='post_likes',
                         weight=2,
                     ),
                     ...
                 ]),
            ...
        ]

    Initialize with a primary user ID and an optional iterable of Posts:

        Stream(1234, [Post(...), ...])

    Posts may otherwise be added as with any other list, (e.g. append, extend);
    Stream addition (+, +=) verifies that both Streams belong to the same user.

    Aggregate analysis is provided through StreamAggregate:

        >>> stream = Stream(1234)
        >>> aggregate = stream.aggregate()
        >>> aggregate[1098].types['post_likes']
        [Interaction(...), ...]

    """
    REPR_OUTPUT_SIZE = 5

    Post = namedtuple('Post', ('post_id', 'message', 'interactions'))
    Interaction = namedtuple('Interaction', ('user_id', 'type', 'weight'))

    class StreamAggregate(defaultdict):
        """Stream data aggregator"""
        UserInteractions = namedtuple('UserInteractions', ('posts', 'types'))

        def __init__(self, stream):
            super(Stream.StreamAggregate, self).__init__(
                lambda: self.UserInteractions(
                    posts=defaultdict(lambda: defaultdict(list)),
                    types=defaultdict(list),
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

    __slots__ = ('user',)

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

    def get_friend_edges(self, token, require_outgoing=False):
        """Retrieve detailed information about a user's network.

        Returns the UserNetwork of Edges between the user and friends.

        (Unlike the module-level function `get_friend_edges`, this method
        performs multiple queries.)

        """
        LOG.debug("getting friend edges from FB for %d", self.user.fbid)
        timer = utils.Timer()

        edges = _get_friend_edges_simple(self.user, token)
        LOG.debug("got %d friends total", len(edges))

        # sort all the friends by their stream rank (if any) and mutual friend count
        aggregate = self.aggregate()
        friend_streamrank = aggregate.ranking()
        LOG.debug("got %d friends ranked", len(friend_streamrank))
        edges.sort(key=lambda edge:
            (friend_streamrank.get(edge.secondary.fbid, sys.maxint),
            -1 * edge.incoming.mut_friends)
        )

        network = datastructs.UserNetwork()
        for (count, edge) in enumerate(edges):
            user_aggregate = aggregate[edge.secondary.fbid]

            user_interactions = user_aggregate.types
            incoming = dynamo.IncomingEdge(
                data=edge.incoming,
                post_likes=len(user_interactions['post_likes']),
                post_comms=len(user_interactions['post_comms']),
                stat_likes=len(user_interactions['stat_likes']),
                stat_comms=len(user_interactions['stat_comms']),
                wall_posts=len(user_interactions['wall_posts']),
                wall_comms=len(user_interactions['wall_comms']),
                tags=len(user_interactions['tags']),
            )

            interactions = {
                dynamo.PostInteractions(
                    user=edge.secondary,
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

            outgoing = edge.outgoing
            if require_outgoing and not outgoing:
                LOG.info("reading friend stream %d/%d (%s)", count, len(edges), edge.secondary.fbid)
                outgoing = self._get_outgoing_edge(edge.secondary, token)

            network.append(
                edge._replace(
                    incoming=incoming,
                    outgoing=outgoing,
                    interactions=interactions,
                )
            )

        LOG.debug("got %d friend edges for %d (%s)", len(network), self.user.fbid, timer)
        return network

    def _get_outgoing_edge(self, friend, token):
        timer = utils.Timer()
        try:
            stream = self.read(friend, token,
                               settings.STREAM_DAYS_OUT,
                               settings.STREAM_DAYS_CHUNK_OUT,
                               settings.STREAM_THREADCOUNT_OUT,
                               settings.STREAM_READ_TIMEOUT_OUT,
                               settings.STREAM_READ_SLEEP_OUT)
        except Exception:
            LOG.warning("error reading stream for %d", friend.fbid, exc_info=True)
            return

        aggregate = stream.aggregate()
        # FIXME: Shouldn't this be user.fbid?
        # TODO: If not, we can add post topics and interactions from this outgoing
        # TODO: stream to the caller's listings of friend interactions.
        # TODO: (But if so, these are the primary's interactions, which are another
        # TODO: story.)
        user_aggregate = aggregate[friend.fbid]
        user_interactions = user_aggregate.types
        LOG.debug('got %s', user_interactions)
        outgoing = dynamo.IncomingEdge(
            fbid_source=self.user.fbid,
            fbid_target=friend.fbid,
            post_likes=len(user_interactions['post_likes']),
            post_comms=len(user_interactions['post_comms']),
            stat_likes=len(user_interactions['stat_likes']),
            stat_comms=len(user_interactions['stat_comms']),
            wall_posts=len(user_interactions['wall_posts']),
            wall_comms=len(user_interactions['wall_comms']),
            tags=len(user_interactions['tags']),
        )

        # Throttling for Facebook limits
        # If this friend took fewer seconds to crawl than the number of chunks, wait that
        # additional time before proceeding to next friend to avoid getting shut out by FB.
        # FIXME: could still run into trouble there if we have to do multiple tries for several chunks.
        # FIXME: and this shouldn't be managed here, as we may wait unnecessarily (e.g. when we're done)
        friend_secs = settings.STREAM_DAYS_OUT / settings.STREAM_DAYS_CHUNK_OUT
        secs_left = friend_secs - timer.elapsed
        if secs_left > 0:
            LOG.debug("Nap time! Waiting %d seconds...", secs_left)
            time.sleep(secs_left)

        return outgoing

    @classmethod
    def read(cls, user, token,
             num_days=settings.STREAM_DAYS_IN,
             chunk_size=settings.STREAM_DAYS_CHUNK_IN,
             thread_count=settings.STREAM_THREADCOUNT_IN,
             loop_timeout=settings.STREAM_READ_TIMEOUT_IN,
             loop_sleep=settings.STREAM_READ_SLEEP_IN):

        user_id = user.fbid
        LOG.debug("Stream.read(%r, %r, %r, %r, %r, %r, %r)",
                  user_id, token[:10] + " ...", num_days,
                  chunk_size, thread_count, loop_timeout, loop_sleep)
        LOG.info('reading stream for user %s', user_id)

        timer = utils.Timer()
        chunk_inputs = Queue.Queue() # fill with (time0, time1) pairs
        chunk_outputs = [] # list of stream obects holding results

        # load the queue
        chunk_size_secs = chunk_size * 24 * 60 * 60
        time_now = int(time.time())
        time_start = time_now - num_days * 24 * 60 * 60
        for time0 in xrange(time_start, time_now, chunk_size_secs):
            time1 = min(time0 + chunk_size_secs, time_now)
            chunk_inputs.put((time0, time1, 0))

        # create the thread pool
        threads = []
        for count in xrange(thread_count):
            thread = StreamReaderThread(
                "%s-%d" % (user_id, count),
                user,
                token,
                chunk_inputs,
                chunk_outputs,
                loop_timeout,
            )
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)

        time_stop = time.time() + loop_timeout
        try:
            while time.time() < time_stop:
                threads = [thread for thread in threads if thread.isAlive()]
                if threads:
                    time.sleep(loop_sleep)
                else:
                    break
        except KeyboardInterrupt:
            LOG.info("ctrl-c, kill 'em all")
            for thread in threads:
                thread.kill_received = True
            LOG.debug("now have %d threads",
                      sum(1 for thread in threads if thread.isAlive()))

        LOG.debug("%d threads still alive after loop", len(threads))
        LOG.debug("%d chunk results for user %s", len(chunk_outputs), user_id)

        num_chunks = num_days / chunk_size # How many chunks should we get back?
        failure_rate = float(num_chunks - len(chunk_outputs)) / num_chunks
        if failure_rate >= settings.BAD_CHUNK_THRESH:
            raise BadChunksError(
                "Aborting Stream.read for %s, bad chunk rate exceeded threshold of %0.2f"
                % (user_id, settings.BAD_CHUNK_THRESH)
            )

        stream = cls(user)
        for (count, chunk) in enumerate(chunk_outputs):
            LOG.debug("chunk %d: %s", count, chunk)
            stream += chunk

        LOG.debug("Stream.read(%r, %r, %r, %r, %r, %r, %r) done in %s",
                  user_id, token[:10] + " ...", num_days, chunk_size,
                  thread_count, loop_timeout, loop_sleep, timer)
        return stream


class StreamReaderThread(threading.Thread):
    """Read a chunk of a user's Stream in a thread"""
    def __init__(self, name, user, token, queue, results, lifespan):
        threading.Thread.__init__(self)
        self.name = name
        self.user = user
        self.token = token
        self.queue = queue
        self.results = results
        self.lifespan = lifespan

    def run(self):
        LOG.debug("Thread %s: starting", self.name)
        time_stop = time.time() + self.lifespan
        timer = utils.Timer()
        count_good = 0
        count_bad = 0
        user_id = self.user.fbid

        while time.time() < time_stop:
            try:
                min_time, max_time, qcount = self.queue.get_nowait()
            except Queue.Empty:
                break

            LOG.debug("Thread %s: reading stream for %s, interval (%s - %s)",
                      self.name, user_id,
                      time.strftime("%m/%d", time.localtime(min_time)),
                      time.strftime("%m/%d", time.localtime(max_time)))
            timer_chunk = utils.Timer()

            stream_label = 'stream'
            wall_label = 'wall_posts'
            stream_ref = '#' + stream_label
            wall_ref = '#' + wall_label
            query = {
                stream_label: fql_stream_chunk(user_id, min_time, max_time),
                wall_label: fql_wall_posts(stream_ref, user_id),
                'post_likes': fql_post_likes(stream_ref),
                'post_comms': fql_post_comms(stream_ref),
                'stat_likes': fql_stat_likes(stream_ref),
                'stat_comms': fql_stat_comms(stream_ref),
                'wall_comms': fql_wall_comms(wall_ref, user_id),
                'tags': fql_tags(stream_ref, user_id),
            }
            try:
                data = urlload('https://graph.facebook.com/fql', {
                    'q': json.dumps(query, separators=(',', ':')), # compact separators
                    'format': 'json',
                    'access_token': self.token,
                })
            except IOError:
                LOG.info(
                    "Thread %s: error reading stream chunk for user %s (%s - %s)",
                    self.name,
                    user_id,
                    time.strftime("%m/%d", time.localtime(min_time)),
                    time.strftime("%m/%d", time.localtime(max_time)),
                    exc_info=True
                )
                count_bad += 1
                self.queue.task_done()
                qcount += 1
                if qcount < settings.STREAM_READ_TRYCOUNT:
                    self.queue.put((min_time, max_time, qcount))
                continue

            results = {entry['name']: entry['fql_result_set']
                       for entry in data['data']}
            stream = Stream(self.user)
            for post_data in results['stream']:
                post = Stream.Post(
                    post_id=post_data['post_id'],
                    message=post_data['message'],
                    interactions=[],
                )
                stream.append(post)
                for (action_type, id_key, rank_weight) in [
                    ('post_likes', 'user_id', 2),
                    ('post_comms', 'fromid', 4),
                    ('stat_likes', 'user_id', 2),
                    ('stat_comms', 'fromid', 4),
                    ('wall_posts', 'actor_id', 2),
                    ('wall_comms', 'actor_id', 4),
                    ('tags', 'tagged_ids', 1),
                ]:
                    for result in results[action_type]:
                        if result['post_id'] == post.post_id:
                            user_ids = result[id_key]
                            if not isinstance(user_ids, list):
                                user_ids = [user_ids]
                            post.interactions.extend(
                                Stream.Interaction(user_id=user_id,
                                                   type=action_type,
                                                   weight=rank_weight)
                                for user_id in user_ids
                            )

            count_good += 1
            self.results.append(stream)
            self.queue.task_done()
            LOG.debug("Thread %s: stream chunk for %s took %s: %s",
                      self.name, user_id, timer_chunk, stream)

        else:
            # We've reached the stop limit
            LOG.debug("Thread %s: reached lifespan, exiting", self.name)

        LOG.debug("Thread %s: finished with %d/%d good (took %s)",
                  self.name, count_good, (count_good + count_bad), timer)


class BadChunksError(IOError):
    """Facebook returned garbage"""
