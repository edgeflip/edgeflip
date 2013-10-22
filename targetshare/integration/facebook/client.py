#!/usr/bin/python
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

PX3_FIELDS = [
    'uid', 'first_name', 'last_name', 'sex', 'birthday_date',
    'current_location', 'mutual_friend_count'
]
PX3_EXTENDED_FIELDS = [
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
]
FULL_PX3_FIELDS = ','.join(PX3_FIELDS + PX3_EXTENDED_FIELDS)

FQL_USER_INFO = """SELECT uid, first_name, last_name, email, sex, birthday_date, current_location FROM user WHERE uid=%s"""
FQL_FRIEND_INFO = """SELECT %s FROM user WHERE uid IN (SELECT uid2 FROM friend where uid1 = %s ORDER BY uid2 LIMIT %s OFFSET %s)"""


def dateFromFb(dateStr):
    """we would like this to die"""
    if (dateStr):
        dateElts = dateStr.split('/')
        if (len(dateElts) == 3):
            m, d, y = dateElts
            return timezone.datetime(int(y), int(m), int(d), tzinfo=timezone.utc)
    return None


def getUrlFb(url):
    """load JSON blob from facebook. facebook is flakey, this deals with that.

    timeout should be parameter, etc.
    """
    try:
        with closing(urllib2.urlopen(url, timeout=settings.FACEBOOK.api_timeout)) as responseFile:
            responseJson = json.load(responseFile)
    except (urllib2.URLError, urllib2.HTTPError) as e:
        logger.info("error opening url %s: %s", url, e.reason)
        try:
            # If we actually got an error back from a server, should be able to read the message here
            logger.error("returned error was: %s", e.read())
        except:
            pass
        raise e

    return responseJson


def _threadFbURL(url, results):
    """Used to read JSON from Facebook in a thread and append output to a list of results"""
    tim = utils.Timer()

    responseJson = getUrlFb(url)
    for entry in responseJson['data']:
        results.append(entry)

    logger.debug('Thread %s read %s records from FB in %s', threading.current_thread().name, len(responseJson['data']), tim.elapsedPr())
    return len(responseJson['data'])


def extendTokenFb(fbid, appid, token):
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


def getFriendsFb(userId, token):
    """retrieve basic info on user's FB friends in a single call,

    returns object from datastructs
    """
    tim = utils.Timer()
    logger.debug("getting friends for %d", userId)

    loopTimeout = settings.FACEBOOK.friendLoop.timeout
    loopSleep = settings.FACEBOOK.friendLoop.sleep
    limit = settings.FACEBOOK.friendLoop.fqlLimit

    # Get the number of friends from FB to determine how many chunks to run
    numFriendsFQL = urllib.quote_plus("SELECT friend_count FROM user WHERE uid = %s" % userId)
    numFriendsURL = 'https://graph.facebook.com/fql?q=' + numFriendsFQL
    numFriendsURL = numFriendsURL + '&format=json&access_token=' + token
    numFriendsJson = getUrlFb(numFriendsURL)

    numFriends = float(numFriendsJson['data'][0]['friend_count'])
    chunks = int(ceil(numFriends / limit)) + 1  # one extra just to be safe

    # Set up the threads for reading the friend info
    threads = []
    friendChunks = []
    for i in range(chunks):
        offset = limit * i
        url = 'https://graph.facebook.com/fql/?q=' + urllib.quote_plus(FQL_FRIEND_INFO % (FULL_PX3_FIELDS, userId, limit, offset))
        url = url + '&format=json&access_token=' + token

        t = threading.Thread(target=_threadFbURL, args=(url, friendChunks))
        t.setDaemon(True)
        t.name = "%s-px3-%d" % (userId, i)
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

    queryJsons.append('"%s":"%s"' % (tagPhotosLabel, urllib.quote_plus(FQL_TAG_PHOTOS % (userId))))
    queryJsons.append('"%s":"%s"' % (primPhotosLabel, urllib.quote_plus(FQL_PRIM_PHOTOS % (tagPhotosRef, userId))))
    queryJsons.append('"primPhotoTags":"%s"' % (urllib.quote_plus(FQL_PRIM_TAGS % (primPhotosRef, userId))))
    queryJsons.append('"%s":"%s"' % (otherPhotosLabel, urllib.quote_plus(FQL_OTHER_PHOTOS % (tagPhotosRef, userId))))
    queryJsons.append('"otherPhotoTags":"%s"' % (urllib.quote_plus(FQL_OTHER_TAGS % (otherPhotosRef, userId))))

    queryJson = '{' + ','.join(queryJsons) + '}'
    photoURL = 'https://graph.facebook.com/fql?q=' + queryJson + '&format=json&access_token=' + token

    photoResults = []
    photoThread = threading.Thread(target=_threadFbURL, args=(photoURL, photoResults))
    photoThread.setDaemon(True)
    photoThread.name = "%s-px3-photos" % userId
    threads.append(photoThread)
    photoThread.start()

    # Loop until all the threads are done
    # or we've run out of time waiting
    timeStop = time.time() + loopTimeout
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

    # Read out the photo data
    lab_recs = {}
    for entry in photoResults:
        label = entry['name']
        records = entry['fql_result_set']
        lab_recs[label] = records

    primPhotoCounts = defaultdict(int)
    otherPhotoCounts = defaultdict(int)

    for rec in lab_recs.get('primPhotoTags', []):
        if (rec['subject']):
            primPhotoCounts[int(rec['subject'])] += 1

    for rec in lab_recs.get('otherPhotoTags', []):
        if (rec['subject']):
            otherPhotoCounts[int(rec['subject'])] += 1

    # A bit of a hack, but using a dictionary to avoid possible duplicates
    # in cases where pagination changes during the query or other FB barf
    # (set() won't work because different instances of FriendInfo with the
    # same friendId are different objects)
    friends = {}
    for rec in friendChunks:
        friendId = int(rec['uid'])
        city = rec['current_location'].get('city') if (rec.get('current_location') is not None) else None
        state = rec['current_location'].get('state') if (rec.get('current_location') is not None) else None
        primPhotoTags = primPhotoCounts[friendId]
        otherPhotoTags = otherPhotoCounts[friendId]
        email = None    # FB won't give you the friends' emails

        if (primPhotoTags + otherPhotoTags > 0):
            logger.debug("Friend %d has %d primary photo tags and %d other photo tags", friendId, primPhotoTags, otherPhotoTags)

        rec.update({
            'city': city, 'state': state, 'email': email,
            'birthday': dateFromFb(rec['birthday_date'])
        })
        f = datastructs.FriendInfo(
            rec, friendId, primPhotoTags, otherPhotoTags, rec['mutual_friend_count']
        )
        friends[friendId] = f
    logger.debug("returning %d friends for %d (%s)", len(friends.values()), userId, tim.elapsedPr())
    return friends.values()


def getUserFb(userId, token):
    """gets more info about primary user from FB

    """
    fql = FQL_USER_INFO % (userId)
    url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=' + token
    responseJson = getUrlFb(url)
    rec = responseJson['data'][0]
    city = rec['current_location'].get('city') if (rec.get('current_location') is not None) else None
    state = rec['current_location'].get('state') if (rec.get('current_location') is not None) else None
    email = rec.get('email')
    rec.update({
        'city': city, 'state': state, 'email': email,
        'birthday': dateFromFb(rec['birthday_date'])
    })
    user = datastructs.UserInfo(rec)
    return user


def getFriendEdges(userId, tok, friendQueue):
    friendQueue.sort(key=lambda x: x.mutuals, reverse=True)
    edges = []
    user = getUserFb(userId, tok)
    for i, friend in enumerate(friendQueue):
        ecIn = datastructs.EdgeCounts(friend.id,
                user.id,
                photoTarg=friend.primPhotoTags,
                photoOth=friend.otherPhotoTags,
                muts=friend.mutuals)
        e = datastructs.Edge(user, friend, ecIn, None)

        edges.append(e)
        logger.debug('friend %s', str(e.secondary))
        logger.debug('edge %s', str(e))  # zzz Edge class no longer has a __str__() method...
                                         #     not important enough to fix for mayors, but maybe should one day?
    return edges


def getFriendEdgesIncoming(userId, tok, friendQueue, requireOutGoing=False):
    logger.info('reading stream for user %s, %s', userId, tok)
    sc = ReadStreamCounts(userId, tok, settings.STREAM_DAYS_IN, settings.STREAM_DAYS_CHUNK_IN, settings.STREAM_THREADCOUNT_IN, loopTimeout=settings.STREAM_READ_TIMEOUT_IN, loopSleep=settings.STREAM_READ_SLEEP_IN)
    logging.debug('got %s', str(sc))
    logger.debug('got %s', str(sc))

    # sort all the friends by their stream rank (if any) and mutual friend count
    friendId_streamrank = dict(enumerate(sc.getFriendRanking()))
    logger.debug("got %d friends ranked", len(friendId_streamrank))
    friendQueue.sort(key=lambda x: (
        friendId_streamrank.get(x.id, sys.maxint), -1 * x.mutuals
    ))
    edges = []
    user = getUserFb(userId, tok)
    for i, friend in enumerate(friendQueue):
        ecOut = None
        ecIn = datastructs.EdgeCounts(
            friend.id,
            user.id,
            postLikes=sc.getPostLikes(friend.id),
            postComms=sc.getPostComms(friend.id),
            statLikes=sc.getStatLikes(friend.id),
            statComms=sc.getStatComms(friend.id),
            wallPosts=sc.getWallPosts(friend.id),
            wallComms=sc.getWallComms(friend.id),
            tags=sc.getTags(friend.id),
            photoTarg=friend.primPhotoTags,
            photoOth=friend.otherPhotoTags,
            muts=friend.mutuals
        )
        if requireOutGoing:
            logger.info("reading friend stream %d/%d (%s)", i, len(friendQueue), friend.id)
            ecOut = getFriendEdgesOutGoing(friend, user, tok)
        e = datastructs.Edge(user, friend, ecIn, ecOut)
        edges.append(e)
        logger.debug('friend %s', str(e.secondary))
        logger.debug('edge %s', str(e))  # zzz Edge class no longer has a __str__() method...

    return edges


def getFriendEdgesOutGoing(friend, user, tok):
    timFriend = utils.Timer()
    try:
        scFriend = ReadStreamCounts(friend.id, tok, settings.STREAM_DAYS_OUT, settings.STREAM_DAYS_CHUNK_OUT, settings.STREAM_THREADCOUNT_OUT, loopTimeout=settings.STREAM_READ_TIMEOUT_OUT, loopSleep=settings.STREAM_READ_SLEEP_OUT)
    except Exception as ex:
        logger.warning("error reading stream for %d: %s", friend.id, str(ex))
        return
    logging.debug('got %s', str(scFriend))

    ecOut = datastructs.EdgeCounts(
        user.id,
        friend.id,
        postLikes=scFriend.getPostLikes(friend.id),
        postComms=scFriend.getPostComms(friend.id),
        statLikes=scFriend.getStatLikes(friend.id),
        statComms=scFriend.getStatComms(friend.id),
        wallPosts=scFriend.getWallPosts(friend.id),
        wallComms=scFriend.getWallComms(friend.id),
        tags=scFriend.getTags(friend.id),
        photoTarg=None,
        photoOth=None,
        muts=None
    )

    # Throttling for Facebook limits
    # If this friend took fewer seconds to crawl than the number of chunks, wait that
    # additional time before proceeding to next friend to avoid getting shut out by FB.
    # __NOTE__: could still run into trouble there if we have to do multiple tries for several chunks.
    friendSecs = settings.STREAM_DAYS_OUT / settings.STREAM_DAYS_CHUNK_OUT
    secsLeft = friendSecs - timFriend.elapsedSecs()
    if (secsLeft > 0):
        logger.debug("Nap time! Waiting %d seconds...", secsLeft)
        time.sleep(secsLeft)
    return ecOut


def getFriendEdgesFb(userId, tok, requireIncoming=False, requireOutgoing=False, skipFriends=None):
    """retrieves user's FB stream and calcs edges b/w user and her friends.

    makes multiple calls to FB! separate calcs & FB calls
    """
    skipFriends = skipFriends if skipFriends is not None else set()

    logger.debug("getting friend edges from FB for %d", userId)
    tim = utils.Timer()
    friends = getFriendsFb(userId, tok)
    logger.debug("got %d friends total", len(friends))

    friendQueue = [f for f in friends if f.id not in skipFriends]
    if requireIncoming:
        edges = getFriendEdgesIncoming(userId, tok, friendQueue, requireOutgoing)
    else:
        edges = getFriendEdges(userId, tok, friendQueue)

    logger.debug("got %d friend edges for %d (%s)", len(edges), userId, tim.elapsedPr())
    return edges


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
        #sys.stderr.write("got post likers: %s\n" % (str(postLikers)))
        #sys.stderr.write("got post commers: %s\n" % (str(postCommers)))
        #sys.stderr.write("got stat likers: %s\n" % (str(statLikers)))
        #sys.stderr.write("got stat commers: %s\n" % (str(statCommers)))
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
