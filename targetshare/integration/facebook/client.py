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
from collections import defaultdict
from contextlib import closing
from itertools import chain
from math import ceil

import requests

from django.conf import settings
from django.utils import timezone

from targetshare import utils
from targetshare.models import datastructs, dynamo


# TODO: This module has been given some but still needs *a lot* of love

logger = logging.getLogger(__name__)


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
    return ("SELECT fromid, post_id FROM comment WHERE post_id IN (SELECT post_id FROM {} WHERE type != {})"
            .format(stream, STREAMTYPE.STATUS_UPDATE))


def fql_post_likes(stream): # TODO: add object_id/url for like targeting?
    return ("SELECT user_id, post_id FROM like WHERE post_id IN (SELECT post_id FROM {} WHERE type != {})"
            .format(stream, STREAMTYPE.STATUS_UPDATE))


def fql_stat_comms(stream):
    return ("SELECT fromid, post_id FROM comment WHERE post_id IN (SELECT post_id FROM {} WHERE type = {})"
            .format(stream, STREAMTYPE.STATUS_UPDATE))


def fql_stat_likes(stream):
    return ("SELECT user_id, post_id FROM like WHERE post_id IN (SELECT post_id FROM {} WHERE type = {})"
            .format(stream, STREAMTYPE.STATUS_UPDATE))


def fql_wall_posts(stream, uid):
    return ("SELECT actor_id, post_id FROM {} WHERE type != {} AND actor_id != {}"
            .format(stream, STREAMTYPE.STATUS_UPDATE, uid))


def fql_wall_comms(wall, uid):
    return ("SELECT actor_id, post_id FROM {0} WHERE post_id IN "
                "(SELECT post_id FROM comment WHERE "
                 "post_id IN (SELECT post_id FROM {0}) AND fromid = {1})"
            .format(wall, uid))


def fql_tags(stream, uid):
    return ("SELECT tagged_ids, post_id FROM {} WHERE actor_id = {} AND type != {}"
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


def urlload(url, query=()):
    """Load data from the given Facebook URL."""
    parsed_url = urlparse.urlparse(url)
    query_params = urlparse.parse_qsl(parsed_url.query)
    query_params.extend(getattr(query, 'items', lambda: query)())
    url = parsed_url._replace(query=urllib.urlencode(query_params)).geturl()

    try:
        with closing(urllib2.urlopen(url, timeout=settings.FACEBOOK.api_timeout)) as response:
            return json.load(response)
    except IOError as exc:
        exc_type, exc_value, trace = sys.exc_info()
        logger.exception("Error opening URL %s %r", url, getattr(exc, 'reason', ''))
        try:
            logger.error("Returned error message was: %s", exc.read())
        except Exception:
            pass
        raise exc_type, exc_value, trace


def _urlload_thread(url, query=(), results=None):
    """Used to read JSON from Facebook in a thread and append output to a list of results"""
    if not hasattr(results, 'extend'):
        raise TypeError("Argument 'results' required and list expected")

    tim = utils.Timer()
    response = urlload(url, query)
    data = response['data']
    results.extend(data)

    logger.debug('Thread %s read %s records from FB in %s',
                 threading.current_thread().name, len(data), tim.elapsedPr())
    return len(data)


def extend_token(fbid, appid, token):
    """Extend lifetime of a user token from FB."""
    url = 'https://graph.facebook.com/oauth/access_token?' + urllib.urlencode({
        'grant_type': 'fb_exchange_token',
        'fb_exchange_token': token,
        'client_id': appid,
        'client_secret': settings.FACEBOOK.secrets[appid],
    })
    ts = time.time()

    # Unfortunately, FB doesn't seem to allow returning JSON for new tokens,
    # even if you try passing &format=json in the URL.
    try:
        with closing(urllib2.urlopen(url, timeout=settings.FACEBOOK.api_timeout)) as response:
            params = urlparse.parse_qs(response.read())
        token1 = params['access_token'][0]
        expires = int(params['expires'][0])
        logging.debug("Extended access token %s expires in %s seconds", token1, expires)
        expires1 = ts + expires
    except (IOError, IndexError, KeyError) as exc:
        if hasattr(exc, 'read'): # built-in hasattr won't overwrite exc_info
            error_response = exc.read()
        else:
            error_response = ''
        logger.warning(
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
    )


def get_friend_edges(user, token, require_incoming=False, require_outgoing=False, skip=()):
    """retrieves user's FB stream and calcs edges b/w user and her friends.

    makes multiple calls to FB! separate calcs & FB calls

    """
    logger.debug("getting friend edges from FB for %d", user.fbid)
    tim = utils.Timer()

    edges = _get_friend_edges_simple(user, token)
    logger.debug("got %d friends total", len(edges))
    if skip:
        edges = [edge for edge in edges if edge.secondary.fbid not in skip]

    if require_incoming:
        edges = _extend_friend_edges(user, token, edges, require_outgoing)
    else:
        edges.sort(key=lambda edge: edge.incoming.mut_friends, reverse=True)

    logger.debug("got %d friend edges for %d (%s)", len(edges), user.fbid, tim.elapsedPr())
    return edges


def _get_friend_edges_simple(user, token):
    """Retrieve basic info on user's FB friends in a single call."""
    tim = utils.Timer()
    logger.debug("getting friends for %d", user.fbid)

    loopTimeout = settings.FACEBOOK.friendLoop.timeout
    loopSleep = settings.FACEBOOK.friendLoop.sleep
    limit = settings.FACEBOOK.friendLoop.fqlLimit

    # Get the number of friends from FB to determine how many chunks to run
    num_friends_response = urlload('https://graph.facebook.com/fql', {
        'q': "SELECT friend_count FROM user WHERE uid = {}".format(user.fbid),
        'format': 'json',
        'access_token': token,
    })
    numFriends = float(num_friends_response['data'][0]['friend_count'])
    chunks = int(ceil(numFriends / limit)) + 1  # one extra just to be safe

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
    timeStop = time.time() + loopTimeout
    while time.time() < timeStop:
        threadsAlive = []
        for t in threads:
            if t.isAlive():
                threadsAlive.append(t)
        threads = threadsAlive
        if threadsAlive:
            time.sleep(loopSleep)
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
    friends = {}
    for rec in friendChunks:
        friendId = int(rec['uid'])
        if friendId in friends:
            continue

        current_location = rec.get('current_location') or {}
        primary_photo_tags = primPhotoCounts[friendId]
        other_photo_tags = otherPhotoCounts[friendId]

        if primary_photo_tags + other_photo_tags > 0:
            logger.debug("Friend %d has %d primary photo tags and %d other photo tags",
                         friendId, primary_photo_tags, other_photo_tags)

        friend = dynamo.User(
            fbid=friendId,
            fname=rec['first_name'],
            lname=rec['last_name'],
            gender=rec['sex'],
            birthday=decode_date(rec['birthday_date']),
            city=current_location.get('city'),
            state=current_location.get('state'),
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

        friends[friend.fbid] = datastructs.Edge(user, friend, edge_data)

    logger.debug("returning %d friends for %d (%s)", len(friends), user.fbid, tim.elapsedPr())
    return friends.values()


def _extend_friend_edges(user, token, edges, require_outgoing=False):
    logger.info('reading stream for user %s, %s', user.fbid, token)
    sc = ReadStreamCounts(
        user.fbid, token, settings.STREAM_DAYS_IN, settings.STREAM_DAYS_CHUNK_IN, settings.STREAM_THREADCOUNT_IN,
        loopTimeout=settings.STREAM_READ_TIMEOUT_IN,
        loopSleep=settings.STREAM_READ_SLEEP_IN)
    logging.debug('got %s', sc)
    logger.debug('got %s', sc)

    # sort all the friends by their stream rank (if any) and mutual friend count
    friend_streamrank = {fbid: position for (position, fbid) in enumerate(sc.getFriendRanking())}
    logger.debug("got %d friends ranked", len(friend_streamrank))
    edges0 = sorted(edges, key=lambda edge:
        (friend_streamrank.get(edge.secondary.fbid, sys.maxint),
         -1 * edge.incoming.mut_friends)
    )

    edges1 = []
    for count, edge in enumerate(edges0):
        friend_id = edge.secondary.fbid
        incoming = dynamo.IncomingEdge(
            data=dict(edge.incoming),
            post_likes=sc.getPostLikes(friend_id),
            post_comms=sc.getPostComms(friend_id),
            stat_likes=sc.getStatLikes(friend_id),
            stat_comms=sc.getStatComms(friend_id),
            wall_posts=sc.getWallPosts(friend_id),
            wall_comms=sc.getWallComms(friend_id),
            tags=sc.getTags(friend_id),
        )

        outgoing = edge.outgoing
        if require_outgoing and not outgoing:
            logger.info("reading friend stream %d/%d (%s)", count, len(edges), friend_id)
            outgoing = _get_outgoing_edge(user, edge.secondary, token)

        edges1.append(edge._replace(incoming=incoming, outgoing=outgoing))

    return edges1


def _get_outgoing_edge(user, friend, token):
    timFriend = utils.Timer()
    try:
        scFriend = ReadStreamCounts(
            friend.fbid, token, settings.STREAM_DAYS_OUT, settings.STREAM_DAYS_CHUNK_OUT, settings.STREAM_THREADCOUNT_OUT,
            loopTimeout=settings.STREAM_READ_TIMEOUT_OUT, loopSleep=settings.STREAM_READ_SLEEP_OUT)
    except Exception as ex:
        logger.warning("error reading stream for %d: %s", friend.fbid, ex)
        return

    logging.debug('got %s', str(scFriend))
    outgoing = dynamo.IncomingEdge(
        fbid_source=user.fbid,
        fbid_target=friend.fbid,
        post_likes=scFriend.getPostLikes(friend.fbid),
        post_comms=scFriend.getPostComms(friend.fbid),
        stat_likes=scFriend.getStatLikes(friend.fbid),
        stat_comms=scFriend.getStatComms(friend.fbid),
        wall_posts=scFriend.getWallPosts(friend.fbid),
        wall_comms=scFriend.getWallComms(friend.fbid),
        tags=scFriend.getTags(friend.fbid),
    )

    # Throttling for Facebook limits
    # If this friend took fewer seconds to crawl than the number of chunks, wait that
    # additional time before proceeding to next friend to avoid getting shut out by FB.
    # FIXME: could still run into trouble there if we have to do multiple tries for several chunks.
    # FIXME: and this shouldn't be managed here, as we may wait unnecessarily (e.g. when we're done)
    friendSecs = settings.STREAM_DAYS_OUT / settings.STREAM_DAYS_CHUNK_OUT
    secsLeft = friendSecs - timFriend.elapsedSecs()
    if secsLeft > 0:
        logger.debug("Nap time! Waiting %d seconds...", secsLeft)
        time.sleep(secsLeft)

    return outgoing


def verify_oauth_code(fb_app_id, code, redirect_uri):
    url_params = {
        'client_id': fb_app_id,
        'redirect_uri': redirect_uri,
        'client_secret': settings.FACEBOOK.secrets[fb_app_id],
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


class StreamAggregate(dict):
    """User stream data struct

    Provides aggregate analysis for data in the form:

        action_type: [(friend_id, post_topic), ...]

    Initialize with a primary user ID and dict initialization arguments:

        StreamAggregate(1234, post_likes=[(0987, 'Health')])

    """
    def __init__(self, user_id, *args, **kws):
        super(StreamAggregate, self).__init__(*args, **kws)
        self.user_id = user_id

    def __iadd__(self, other):
        if self.user_id != other.user_id:
            raise ValueError("StreamAggregates belong to different users")
        keys = set(self)
        other_keys = set(other)
        for action_type in (keys & other_keys):
            self[action_type] = tuple(chain(self[action_type], other[action_type]))
        for action_type in (other_keys - keys):
            self[action_type] = tuple(other[action_type])
        return self # FIXME: Needed?

    def __add__(self, other):
        new = type(self)(self.user_id)
        new += self
        new += other
        return new

    # TODO: start here (replace all these dumb things, probably with a single
    # method or two):
    def addPostLikers(self, friendIds):
        for friendId in friendIds:
            self.friendId_postLikeCount[friendId] += 1

    def addPostCommers(self, friendIds):
        for friendId in friendIds:
            self.friendId_postCommCount[friendId] += 1

    def addStatLikers(self, friendIds):
        for friendId in friendIds:
            self.friendId_statLikeCount[friendId] += 1

    def addStatCommers(self, friendIds):
        for friendId in friendIds:
            self.friendId_statCommCount[friendId] += 1

    def addWallPosters(self, friendIds):
        for friendId in friendIds:
            self.friendId_wallPostCount[friendId] += 1

    def addWallCommeds(self, friendIds):
        for friendId in friendIds:
            self.friendId_wallCommCount[friendId] += 1

    def addTaggeds(self, friendIds):
        for friendId in friendIds:
            self.friendId_tagCount[friendId] += 1

    def getPostLikes(self, friendId):
        return self.friendId_postLikeCount.get(friendId, 0)

    def getPostComms(self, friendId):
        return self.friendId_postCommCount.get(friendId, 0)

    def getStatLikes(self, friendId):
        return self.friendId_statLikeCount.get(friendId, 0)

    def getStatComms(self, friendId):
        return self.friendId_statCommCount.get(friendId, 0)

    def getWallPosts(self, friendId):
        return self.friendId_wallPostCount.get(friendId, 0)

    def getWallComms(self, friendId):
        return self.friendId_wallCommCount.get(friendId, 0)

    def getTags(self, friendId):
        return self.friendId_tagCount.get(friendId, 0)

    def getFriendIds(self):
        fIds = set()
        fIds.update(self.friendId_postLikeCount.keys())
        fIds.update(self.friendId_postCommCount.keys())
        fIds.update(self.friendId_statLikeCount.keys())
        fIds.update(self.friendId_statCommCount.keys())
        fIds.update(self.friendId_wallPostCount.keys())
        fIds.update(self.friendId_wallCommCount.keys())
        fIds.update(self.friendId_tagCount.keys())
        return fIds

    def getFriendRanking(self):
        """preliminary ranking used to decide which friends to crawl

        """
        fIds = self.getFriendIds()
        friendId_total = defaultdict(int)
        for fId in fIds:
            friendId_total[fId] += self.friendId_postLikeCount.get(fId, 0) * 2
            friendId_total[fId] += self.friendId_postCommCount.get(fId, 0) * 4
            friendId_total[fId] += self.friendId_statLikeCount.get(fId, 0) * 2
            friendId_total[fId] += self.friendId_statCommCount.get(fId, 0) * 4
            friendId_total[fId] += self.friendId_wallPostCount.get(fId, 0) * 2 # guessed weight
            friendId_total[fId] += self.friendId_wallCommCount.get(fId, 0) * 4 # guessed weight
            friendId_total[fId] += self.friendId_tagCount.get(fId, 0) * 1         # guessed weight
        return sorted(fIds, key=lambda x: friendId_total[x], reverse=True)


class ReadStreamCounts(StreamAggregate):
    """does work of reading a single user's stream

    i need to be refactored
    """
    def __init__(self, userId, token, numDays=100, chunkSizeDays=20, threadCount=4, timeout=settings.FACEBOOK.api_timeout, loopTimeout=10, loopSleep=0.1):
        # zzz Is the "timeout" param even getting used here? Appears to be leftover from an earlier version...

        logger.debug("ReadStreamCounts(%s, %s, %d, %d, %d)", userId, token[:10] + "...", numDays, chunkSizeDays, threadCount)
        tim = utils.Timer()
        self.id = userId
        self.stream = []
        self.friendId_postLikeCount = defaultdict(int)
        self.friendId_postCommCount = defaultdict(int)
        self.friendId_statLikeCount = defaultdict(int)
        self.friendId_statCommCount = defaultdict(int)
        self.friendId_wallPostCount = defaultdict(int)
        self.friendId_wallCommCount = defaultdict(int)
        self.friendId_tagCount = defaultdict(int)

        tsQueue = Queue.Queue() # fill with (t1, t2) pairs
        scChunks = [] # list of sc obects holding results

        numChunks = numDays / chunkSizeDays # How many chunks should we get back?

        # load the queue
        chunkSizeSecs = chunkSizeDays * 24 * 60 * 60
        tsNow = int(time.time())
        tsStart = tsNow - numDays * 24 * 60 * 60
        for ts1 in range(tsStart, tsNow, chunkSizeSecs):
            ts2 = min(ts1 + chunkSizeSecs, tsNow)
            tsQueue.put((ts1, ts2, 0))

        # create the thread pool
        threads = []
        for i in range(threadCount):
            t = ThreadStreamReader(
                "%s-%d" % (userId, i),
                userId,
                token,
                tsQueue,
                scChunks,
                loopTimeout,
            )
            t.setDaemon(True)
            threads.append(t)
            t.start()

        timeStop = time.time() + loopTimeout
        try:
            while (time.time() < timeStop):
                threadsAlive = []
                for t in threads:
                    if t.isAlive():
                        threadsAlive.append(t)
                threads = threadsAlive
                if (threadsAlive):
                    time.sleep(loopSleep)
                else:
                    break

        except KeyboardInterrupt:
            logger.info("ctrl-c, kill 'em all")
            for t in threads:
                t.kill_received = True
            tc = len([t for t in threads if t.isAlive()])
            logger.debug("now have %d threads", tc)

        logger.debug("%d threads still alive after loop", len(threads))
        logger.debug("%d chunk results for user %s", len(scChunks), userId)

        badChunkRate = 1.0 * (numChunks - len(scChunks)) / numChunks
        if (badChunkRate >= settings.BAD_CHUNK_THRESH):
            raise BadChunksError("Aborting ReadStreamCounts for %s: bad chunk rate exceeded threshold of %0.2f" % (userId, settings.BAD_CHUNK_THRESH))

        for i, scChunk in enumerate(scChunks):
            logger.debug("chunk %d %s", i, str(scChunk))
            self.__iadd__(scChunk)
        logger.debug("ReadStreamCounts(%s, %s, %d, %d, %d) done %s", userId, token[:10] + "...", numDays, chunkSizeDays, threadCount, tim.elapsedPr())


class ThreadStreamReader(threading.Thread):
    """implements work of ReadStreamCounts

    """
    def __init__(self, name, primary_id, token, queue, results, lifespan):
        threading.Thread.__init__(self)
        self.name = name
        self.primary_id = primary_id
        self.token = token
        self.queue = queue
        self.results = results
        self.lifespan = lifespan

    def run(self):
        time_stop = time.time() + self.lifespan
        logger.debug("thread %s starting", self.name)
        timThread = utils.Timer()
        goodCount = 0
        errCount = 0
        while time.time() < time_stop:
            try:
                ts1, ts2, qcount = self.queue.get_nowait()
            except Queue.Empty:
                break

            tim = utils.Timer()

            logger.debug("reading stream for %s, interval (%s - %s)",
                         self.primary_id, time.strftime("%m/%d", time.localtime(ts1)), time.strftime("%m/%d", time.localtime(ts2)))

            stream_label = 'stream'
            wall_label = 'wallPosts'
            stream_ref = '#' + stream_label
            wall_ref = '#' + wall_label
            query = {
                stream_label: fql_stream_chunk(self.primary_id, ts1, ts2),
                wall_label: fql_wall_posts(stream_ref, self.primary_id),
                'post_likes': fql_post_likes(stream_ref),
                'post_comms': fql_post_comms(stream_ref),
                'stat_likes': fql_stat_likes(stream_ref),
                'stat_comms': fql_stat_comms(stream_ref),
                'wall_comms': fql_wall_comms(wall_ref, self.primary_id),
                'tags': fql_tags(stream_ref, self.primary_id),
            }
            try:
                data = urlload('https://graph.facebook.com/fql', {
                    'q': json.dumps(query, separators=(',', ':')), # compact separators
                    'format': 'json',
                    'access_token': self.token,
                })
            except IOError:
                logger.error("error reading stream chunk for user %s (%s - %s)",
                             self.primary_id, time.strftime("%m/%d", time.localtime(ts1)), time.strftime("%m/%d", time.localtime(ts2)))
                errCount += 1
                self.queue.task_done()
                qcount += 1
                if qcount < settings.STREAM_READ_TRYCOUNT:
                    self.queue.put((ts1, ts2, qcount))
                continue

            with open('/tmp/stream' + self.name, 'w') as fh: # TODO: REMOVE
                fh.write(json.dumps(data)) # TODO: REMOVE

            results = {entry['name']: entry['fql_result_set']
                       for entry in data['data']}
            post_topics = {post['post_id']: classify(post['message'])
                           for post in results['stream']}
            # TODO: classify post messages here? and attach classifications to
            # secondaries' likes/comments?
            # TODO: can perhaps take custom classifications as well, which
            # might require text-search rather than using the search tool
            # TODO: and if this gets expensive, can instead not default to all
            # topics, though will want to *be careful not to overwrite* existing
            # Edge topic data.
            post_actions = {
                action_type: [(result[id_key], post_topics[result['post_id']])
                              for result in results[action_type]]
                for (action_type, id_key) in [
                    ('post_likes', 'user_id'),
                    ('post_comms', 'fromid'),
                    ('stat_likes', 'user_id'),
                    ('stat_comms', 'fromid'),
                    ('wallPosts', 'actor_id'),
                    ('wall_comms', 'actor_id'),
                ]
            }
            post_actions['tags'] = [
                (user, result['post_id'])
                for result in results['tags']
                for user in result['tagged_ids']
            ]
            sc = StreamAggregate(self.primary_id, results['stream'],
                              pLikeIds, pCommIds, sLikeIds, sCommIds, wPostIds, wCommIds, tagIds)

            logger.debug("stream counts for %s: %s", self.primary_id, str(sc))
            logger.debug("chunk took %s", tim.elapsedPr())

            goodCount += 1
            self.results.append(sc)
            self.queue.task_done()

        else: # we've reached the stop limit
            logger.debug("thread %s reached lifespan, exiting", self.name)

        logger.debug("thread %s finishing with %d/%d good (took %s)", self.name, goodCount, (goodCount + errCount), timThread.elapsedPr())


class BadChunksError(IOError):
    """facebook returned garbage"""


def classify(_text):
    """Dummy text classifier."""
    # TODO: REMOVE
    return {'Health:Heart Disease': 8.2,
            'Sports': 0.3,
            'Sports:Badmitton': 0.2}
