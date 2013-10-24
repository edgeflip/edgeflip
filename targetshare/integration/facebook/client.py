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
from math import ceil

from django.conf import settings
from django.utils import timezone

from targetshare import utils
from targetshare.models import datastructs, dynamo


# TODO: This module has been given some but still needs *a lot* of love

logger = logging.getLogger(__name__)


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

"""stock queries for facebook

these all need to be functions
"""

FQL_STREAM_CHUNK = " ".join("""SELECT created_time, post_id, source_id, target_id, type, actor_id, tagged_ids FROM stream
                                WHERE source_id=%s AND %d <= created_time AND created_time < %d LIMIT 5000""".split())
FQL_POST_COMMS = "SELECT fromid FROM comment WHERE post_id IN (SELECT post_id FROM %s WHERE type != " + str(STREAMTYPE.STATUS_UPDATE) + ")"
FQL_POST_LIKES = "SELECT user_id FROM like WHERE post_id IN (SELECT post_id FROM %s WHERE type != " + str(STREAMTYPE.STATUS_UPDATE) + ")"
FQL_STAT_COMMS = "SELECT fromid FROM comment WHERE post_id IN (SELECT post_id FROM %s WHERE type = " + str(STREAMTYPE.STATUS_UPDATE) + ")"
FQL_STAT_LIKES = "SELECT user_id FROM like WHERE post_id IN (SELECT post_id FROM %s WHERE type = " + str(STREAMTYPE.STATUS_UPDATE) + ")"
FQL_WALL_POSTS = "SELECT actor_id, post_id FROM %s WHERE type != " + str(STREAMTYPE.STATUS_UPDATE) + " AND actor_id != %s"
FQL_WALL_COMMS = "SELECT actor_id FROM %s WHERE post_id IN (SELECT post_id FROM comment WHERE post_id IN (SELECT post_id FROM %s) AND fromid = %s)"
FQL_TAGS = "SELECT tagged_ids FROM %s WHERE actor_id = %s AND type != " + str(STREAMTYPE.PHOTO)
#zzz perhaps this will tighten these up: http://facebook.stackoverflow.com/questions/10836965/get-posts-made-by-facebook-friends-only-on-page-through-graphapi/10837566#10837566

FQL_TAG_PHOTOS = "SELECT object_id FROM photo_tag WHERE subject = %s"
FQL_PRIM_PHOTOS = "SELECT object_id FROM photo WHERE object_id IN (SELECT object_id FROM %s) AND owner = %s"
FQL_PRIM_TAGS = "SELECT subject FROM photo_tag WHERE object_id IN (SELECT object_id FROM %s) AND subject != %s"
FQL_OTHER_PHOTOS = "SELECT object_id FROM photo WHERE object_id IN (SELECT object_id FROM %s) AND owner != %s"
FQL_OTHER_TAGS = "SELECT subject FROM photo_tag WHERE object_id IN (SELECT object_id FROM %s) AND subject != %s"
# Could probably combine these to get rid of the separate "photo" queries, but then each would contain two nested subqueries. Not sure what's worse with FQL.

FQL_USER_INFO = """SELECT uid, first_name, last_name, email, sex, birthday_date, current_location FROM user WHERE uid=%s"""
FQL_FRIEND_INFO = """SELECT uid, first_name, last_name, sex, birthday_date, current_location, mutual_friend_count FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = %s ORDER BY uid2 LIMIT %s OFFSET %s)"""


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
    fql = FQL_USER_INFO % uid
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
                'q': FQL_FRIEND_INFO % (user.fbid, limit, offset),
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

    queryJsons = []

    tagPhotosLabel = "tag_photos"
    primPhotosLabel = "prim_photos"
    otherPhotosLabel = "other_photos"
    tagPhotosRef = "#" + tagPhotosLabel
    primPhotosRef = "#" + primPhotosLabel
    otherPhotosRef = "#" + otherPhotosLabel

    queryJsons.append('"%s":"%s"' % (tagPhotosLabel, FQL_TAG_PHOTOS % user.fbid))
    queryJsons.append('"%s":"%s"' % (primPhotosLabel, FQL_PRIM_PHOTOS % (tagPhotosRef, user.fbid)))
    queryJsons.append('"primPhotoTags":"%s"' % (FQL_PRIM_TAGS % (primPhotosRef, user.fbid)))
    queryJsons.append('"%s":"%s"' % (otherPhotosLabel, FQL_OTHER_PHOTOS % (tagPhotosRef, user.fbid)))
    queryJsons.append('"otherPhotoTags":"%s"' % (FQL_OTHER_TAGS % (otherPhotosRef, user.fbid)))

    photoResults = []
    photoThread = threading.Thread(target=_urlload_thread, args=(
        'https://graph.facebook.com/fql',
        {
            'q': '{' + ','.join(queryJsons) + '}',
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

    for rec in lab_recs.get('primPhotoTags', []):
        if rec['subject']:
            primPhotoCounts[int(rec['subject'])] += 1

    for rec in lab_recs.get('otherPhotoTags', []):
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
        primPhotoTags = primPhotoCounts[friendId]
        otherPhotoTags = otherPhotoCounts[friendId]

        if primPhotoTags + otherPhotoTags > 0:
            logger.debug("Friend %d has %d primary photo tags and %d other photo tags",
                         friendId, primPhotoTags, otherPhotoTags)

        friend = dynamo.User(
            fbid=friendId,
            fname=rec['first_name'],
            lname=rec['last_name'],
            gender=rec['sex'],
            birthday=decode_date(rec['birthday_date']),
            city=current_location.get('city'),
            state=current_location.get('state'),
        )
        edge_data = dynamo.IncomingEdge(
            fbid_source=friend.fbid,
            fbid_target=user.fbid,
            photos_target=primPhotoTags,
            photos_other=otherPhotoTags,
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
    friend_streamrank = dict(enumerate(sc.getFriendRanking()))
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


class StreamCounts(object):
    """data structure representing a single facebook user stream

    intermediary data structure

    we would like this die
    """
    def __init__(self, userId, stream=None, postLikers=None, postCommers=None, statLikers=None, statCommers=None, wallPosters=None, wallCommeds=None, taggeds=None):

        stream = stream if stream is not None else []
        postLikers = postLikers if postLikers is not None else []
        postCommers = postCommers if postCommers is not None else []
        statLikers = statLikers if statLikers is not None else []
        statCommers = statCommers if statCommers is not None else []
        wallPosters = wallPosters if wallPosters is not None else []
        wallCommeds = wallCommeds if wallCommeds is not None else []
        taggeds = taggeds if taggeds is not None else []

        self.id = userId
        self.stream = []
        self.friendId_postLikeCount = defaultdict(int)
        self.friendId_postCommCount = defaultdict(int)
        self.friendId_statLikeCount = defaultdict(int)
        self.friendId_statCommCount = defaultdict(int)
        self.friendId_wallPostCount = defaultdict(int)
        self.friendId_wallCommCount = defaultdict(int)
        self.friendId_tagCount = defaultdict(int)
        self.friendId_tagCount = defaultdict(int)

        self.stream.extend(stream)
        self.addPostLikers(postLikers)
        self.addPostCommers(postCommers)
        self.addStatLikers(statLikers)
        self.addStatCommers(statCommers)
        self.addWallPosters(wallPosters)
        self.addWallCommeds(wallCommeds)
        self.addTaggeds(taggeds)

    def __iadd__(self, other):
        self.stream.extend(other.stream)
        for fId, cnt in other.friendId_postLikeCount.items():
            self.friendId_postLikeCount[fId] += cnt
        for fId, cnt in other.friendId_postCommCount.items():
            self.friendId_postCommCount[fId] += cnt
        for fId, cnt in other.friendId_statLikeCount.items():
            self.friendId_statLikeCount[fId] += cnt
        for fId, cnt in other.friendId_statCommCount.items():
            self.friendId_statCommCount[fId] += cnt
        for fId, cnt in other.friendId_wallPostCount.items():
            self.friendId_wallPostCount[fId] += cnt
        for fId, cnt in other.friendId_wallCommCount.items():
            self.friendId_wallCommCount[fId] += cnt
        for fId, cnt in other.friendId_tagCount.items():
            self.friendId_tagCount[fId] += cnt
        return self

    def __add__(self, other):
        """XXX wrong Exception"""
        if (self.id != other.id):
            raise Exception("cannot add stream counts for different users (%d, %d)" % (self.id, other.id))
        sc = StreamCounts(self.id)
        sc += self
        sc += other
        return sc

    def __str__(self):
        ret = "%d entries" % (len(self.stream))
        ret += ", %d post likes" % (sum(self.friendId_postLikeCount.values()))
        ret += ", %d post comments" % (sum(self.friendId_postCommCount.values()))
        ret += ", %d stat likes" % (sum(self.friendId_statLikeCount.values()))
        ret += ", %d stat comments" % (sum(self.friendId_statCommCount.values()))
        ret += ", %d wall posts" % (sum(self.friendId_wallPostCount.values()))
        ret += ", %d wall comms" % (sum(self.friendId_wallCommCount.values()))
        ret += ", %d tags" % (sum(self.friendId_tagCount.values()))
        return ret

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


class ReadStreamCounts(StreamCounts):
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
            t = ThreadStreamReader(userId, token, tsQueue, scChunks, loopTimeout)
            t.setDaemon(True)
            t.name = "%s-%d" % (userId, i)
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
    def __init__(self, userId, token, queue, results, lifespan):
        threading.Thread.__init__(self)
        self.userId = userId
        self.token = token
        self.queue = queue
        self.results = results
        self.lifespan = lifespan

    def run(self):
        timeStop = time.time() + self.lifespan
        logger.debug("thread %s starting", self.name)
        timThread = utils.Timer()
        goodCount = 0
        errCount = 0
        while (time.time() < timeStop):
            try:
                ts1, ts2, qcount = self.queue.get_nowait()
            except Queue.Empty as e:
                break

            tim = utils.Timer()

            logger.debug("reading stream for %s, interval (%s - %s)", self.userId, time.strftime("%m/%d", time.localtime(ts1)), time.strftime("%m/%d", time.localtime(ts2)))

            queryJsons = []
            streamLabel = "stream"
            wallPostsLabel = "wallPosts"
            queryJsons.append('"%s":"%s"' % (streamLabel, urllib.quote_plus(FQL_STREAM_CHUNK % (self.userId, ts1, ts2))))
            streamRef = "#" + streamLabel
            wallPostsRef = "#" + wallPostsLabel
            queryJsons.append('"postLikes":"%s"' % (urllib.quote_plus(FQL_POST_LIKES % (streamRef))))
            queryJsons.append('"postComms":"%s"' % (urllib.quote_plus(FQL_POST_COMMS % (streamRef))))
            queryJsons.append('"statLikes":"%s"' % (urllib.quote_plus(FQL_STAT_LIKES % (streamRef))))
            queryJsons.append('"statComms":"%s"' % (urllib.quote_plus(FQL_STAT_COMMS % (streamRef))))
            queryJsons.append('"%s":"%s"' % (wallPostsLabel, urllib.quote_plus(FQL_WALL_POSTS % (streamRef, self.userId))))
            queryJsons.append('"wallComms":"%s"' % (urllib.quote_plus(FQL_WALL_COMMS % (wallPostsRef, wallPostsRef, self.userId))))
            queryJsons.append('"tags":"%s"' % (urllib.quote_plus(FQL_TAGS % (streamRef, self.userId))))
            queryJson = '{' + ','.join(queryJsons) + '}'

            url = 'https://graph.facebook.com/fql?q=' + queryJson + '&format=json&access_token=' + self.token

            req = urllib2.Request(url)
            try:
                responseFile = urllib2.urlopen(req, timeout=settings.FACEBOOK.api_timeout)
            except Exception as e:
                logger.error("error reading stream chunk for user %s (%s - %s): %s", self.userId, time.strftime("%m/%d", time.localtime(ts1)), time.strftime("%m/%d", time.localtime(ts2)), str(e))

                try:
                    # If we actually got an error back from a server, should be able to read the message here
                    logger.error("returned error was: %s", e.read())
                except:
                    pass
                errCount += 1
                self.queue.task_done()
                qcount += 1
                if (qcount < settings.STREAM_READ_TRYCOUNT):
                    self.queue.put((ts1, ts2, qcount))
                continue

            responseJson = json.load(responseFile)
            responseFile.close()

            lab_recs = {}
            for entry in responseJson['data']:
                label = entry['name']
                records = entry['fql_result_set']

                lab_recs[label] = records

            pLikeIds = [r['user_id'] for r in lab_recs['postLikes']]
            pCommIds = [r['fromid'] for r in lab_recs['postComms']]
            sLikeIds = [r['user_id'] for r in lab_recs['statLikes']]
            sCommIds = [r['fromid'] for r in lab_recs['statComms']]
            wPostIds = [r['actor_id'] for r in lab_recs['wallPosts']]
            wCommIds = [r['actor_id'] for r in lab_recs['wallComms']]
            tagIds = [i for r in lab_recs['tags'] for i in r['tagged_ids']]
            sc = StreamCounts(self.userId, lab_recs['stream'], pLikeIds, pCommIds, sLikeIds, sCommIds, wPostIds, wCommIds, tagIds)

            logger.debug("stream counts for %s: %s", self.userId, str(sc))
            logger.debug("chunk took %s", tim.elapsedPr())

            goodCount += 1

            self.results.append(sc)
            self.queue.task_done()

        else: # we've reached the stop limit
            logger.debug("thread %s reached lifespan, exiting", self.name)

        logger.debug("thread %s finishing with %d/%d good (took %s)", self.name, goodCount, (goodCount + errCount), timThread.elapsedPr())


class BadChunksError(Exception):
    """facebook returned garbage"""
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
