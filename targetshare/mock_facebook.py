#!/usr/bin/python
"""Module to mock out talking to Facebook for load testing

NOTE: This is built around our current implementation with
      just px3 and minimal edges. We'll need to do something
      more if we want to move to more complex edges.

"""
import time
import datetime
import urllib
import random
import logging
from collections import defaultdict

from django.conf import settings
from django.utils import timezone

from targetshare.models import datastructs


logger = logging.getLogger(__name__)


"""Some fake names for generating friends.

These will work for state-based filtes; not great for ethnicity-based.

"""
FIRST_NAMES = ['Larry', 'Darryl', 'Darryl', 'Bob', 'Bart', 'Lisa', 'Maggie', 'Homer', 'Marge', 'Dude', 'Jeffrey', 'Keyser', 'Ilsa']
LAST_NAMES = ['Newhart', 'Simpson', 'Lebowski', 'Soze', 'Lund', 'Smith', 'Doe']
CITY_NAMES = ['Casablanca', 'Sprinfield', 'Shelbyville', 'Nowhere', 'Capital City']
STATE_NAMES = ['Alabama', 'Alaska', 'American Samoa', 'Arizona', 'Arkansas',
    'California', 'Colorado', 'Connecticut', 'Delaware', 'District of Columbia',
    'Florida', 'Georgia', 'Guam', 'Hawaii', 'Idaho', 'Illinois', 'Indiana',
    'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts',
    'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'National',
    'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
    'North Carolina', 'North Dakota', 'Northern Mariana Islands', 'Ohio',
    'Oklahoma', 'Oregon', 'Pennsylvania', 'Puerto Rico', 'Rhode Island',
    'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
    'Virgin Islands', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin',
    'Wyoming']


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
FQL_TAGS       = "SELECT tagged_ids FROM %s WHERE actor_id = %s AND type != " + str(STREAMTYPE.PHOTO)
#zzz perhaps this will tighten these up: http://facebook.stackoverflow.com/questions/10836965/get-posts-made-by-facebook-friends-only-on-page-through-graphapi/10837566#10837566

FQL_TAG_PHOTOS   = "SELECT object_id FROM photo_tag WHERE subject = %s"
FQL_PRIM_PHOTOS  = "SELECT object_id FROM photo WHERE object_id IN (SELECT object_id FROM %s) AND owner = %s"
FQL_PRIM_TAGS    = "SELECT subject FROM photo_tag WHERE object_id IN (SELECT object_id FROM %s) AND subject != %s"
FQL_OTHER_PHOTOS = "SELECT object_id FROM photo WHERE object_id IN (SELECT object_id FROM %s) AND owner != %s"
FQL_OTHER_TAGS   = "SELECT subject FROM photo_tag WHERE object_id IN (SELECT object_id FROM %s) AND subject != %s"
# Could probably combine these to get rid of the separate "photo" queries, but then each would contain two nested subqueries. Not sure what's worse with FQL.

FQL_USER_INFO   = """SELECT uid, first_name, last_name, email, sex, birthday_date, current_location FROM user WHERE uid=%s"""
FQL_FRIEND_INFO = """SELECT uid, first_name, last_name, sex, birthday_date, current_location, mutual_friend_count FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = %s)"""


def dateFromFb(dateStr):
    """we would like this to die"""
    if (dateStr):
        dateElts = dateStr.split('/')
        if (len(dateElts) == 3):
            m, d, y = dateElts
            return timezone.datetime(int(y), int(m), int(d), tzinfo=timezone.utc)
    return None


def extendTokenFb(user, token, appid):
    """extends lifetime of a user token from FB, which doesn't return JSON
    """
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token' + '&fb_exchange_token=%s' % token.tok
    url += '&client_id=' + str(appid) + '&client_secret=' + settings.FACEBOOK.secrets[appid]
    # Unfortunately, FB doesn't seem to allow returning JSON for new tokens,
    # even if you try passing &format=json in the URL.
    ts = time.time()

    # just return the current token without talking to FB...
    responseDict = {'access_token': [token.tok], 'expires': ['5184000']}
    tokNew = responseDict['access_token'][0]
    expiresIn = int(responseDict['expires'][0])
    logging.debug("Mocked extended access token %s expires in %s seconds." % (tokNew, expiresIn))
    expDate = timezone.make_aware(
        datetime.datetime.utcfromtimestamp(ts + expiresIn),
        timezone.utc
    )
    return datastructs.TokenInfo(tokNew, user, appid, expDate)


def fakeUserInfo(fbid, friend=False, numFriends=0):
    fakeInfo = {}
    fakeInfo['uid'] = fbid
    fakeInfo['sex'] = u'male' if random.random() < 0.5 else u'female'
    fakeInfo['first_name'] = unicode(random.choice(FIRST_NAMES))
    fakeInfo['last_name'] = unicode(random.choice(LAST_NAMES))

    if (random.random() <= 0.33):
        fakeInfo['birthday_date'] = '%s/%s/%s' % (random.randint(1, 12), random.randint(1, 28), random.randint(1920, 1995))
    else:
        fakeInfo['birthday_date'] = None

    if (random.random() <= 0.67):
        fakeInfo['current_location'] = {
            'city': unicode(random.choice(CITY_NAMES)),
            'state': unicode(random.choice(STATE_NAMES))
        }

    if (friend):
        # Only have a mutual friend count for friends
        fakeInfo['mutual_friend_count'] = random.randint(0, numFriends)
    else:
        # Only get an email for primaries
        fakeInfo['email'] = u'fake@fake.com'

    return fakeInfo


def getFriendsFb(userId, token):
    """retrieve basic info on user's FB friends in a single call,

    returns object from datastructs
    """
    tim = datastructs.Timer()
    logger.debug("mocking getting friends for %d", userId)

    # Photo stuff should return quickly enough that we can grab it at the same time as getting friend info

    queryJsons = []

    tagPhotosLabel = "tag_photos"
    primPhotosLabel = "prim_photos"
    otherPhotosLabel = "other_photos"
    tagPhotosRef = "#" + tagPhotosLabel
    primPhotosRef = "#" + primPhotosLabel
    otherPhotosRef = "#" + otherPhotosLabel

    queryJsons.append('"friendInfo":"%s"' % (urllib.quote_plus(FQL_FRIEND_INFO % (userId))))
    queryJsons.append('"%s":"%s"' % (tagPhotosLabel, urllib.quote_plus(FQL_TAG_PHOTOS % (userId))))
    queryJsons.append('"%s":"%s"' % (primPhotosLabel, urllib.quote_plus(FQL_PRIM_PHOTOS % (tagPhotosRef, userId))))
    queryJsons.append('"primPhotoTags":"%s"' % (urllib.quote_plus(FQL_PRIM_TAGS % (primPhotosRef, userId))))
    queryJsons.append('"%s":"%s"' % (otherPhotosLabel, urllib.quote_plus(FQL_OTHER_PHOTOS % (tagPhotosRef, userId))))
    queryJsons.append('"otherPhotoTags":"%s"' % (urllib.quote_plus(FQL_OTHER_TAGS % (otherPhotosRef, userId))))

    queryJson = '{' + ','.join(queryJsons) + '}'
    url = 'https://graph.facebook.com/fql?q=' + queryJson + '&format=json&access_token=%s' % token

    # zzz Should this also wait for a couple of seconds to mock out
    #     tying up the thread while we wait for a resonse from the
    #     Facebook API??
    # TODO: Stop using this mock_facebook lib for unit tests, and instead
    # use the Mock lib. Then we can drop this check, and
    # stick with using this library for its other real purposes.
    if settings.DEBUG:
        time.sleep(random.random()*4+0.5)

    # generate fake id's for between 1 and 1,000 fake friends
    # note - adding 100000000000 because this appears to fall into a gap in read fbid's
    # (just an extra bit of security against accidently overwriting real data...)
    fakeFriendIds = set([100000000000+random.randint(1,10000000) for i in range(random.randint(1,1000))])
    fakeFriendIds = list(fakeFriendIds)
    numFakeFriends = len(fakeFriendIds)

    responseJson = { 'data' :
      [
        {
            'name' : 'primPhotoTags',
            'fql_result_set' : [{'subject' : str(random.choice(fakeFriendIds))} for i in range(random.randint(0, 500))]
        },
        {
            'name' : 'otherPhotoTags',
            'fql_result_set' : [{'subject' : str(random.choice(fakeFriendIds))} for i in range(random.randint(0, 25000))]
        },
        {
            'name' : 'friendInfo',
            'fql_result_set' : [fakeUserInfo(fbid, friend=True, numFriends=numFakeFriends) for fbid in fakeFriendIds]
        }
      ]
    }

    lab_recs = {}
    for entry in responseJson['data']:
        label = entry['name']
        records = entry['fql_result_set']
        lab_recs[label] = records

    primPhotoCounts = defaultdict(int)
    otherPhotoCounts = defaultdict(int)

    for rec in lab_recs['primPhotoTags']:
        if (rec['subject']):
            primPhotoCounts[int(rec['subject'])] += 1

    for rec in lab_recs['otherPhotoTags']:
        if (rec['subject']):
            otherPhotoCounts[int(rec['subject'])] += 1

    friends = []
    for rec in lab_recs['friendInfo']:
        friendId = rec['uid']
        city = rec['current_location'].get('city') if (rec.get('current_location') is not None) else None
        state = rec['current_location'].get('state') if (rec.get('current_location') is not None) else None
        primPhotoTags = primPhotoCounts[friendId]
        otherPhotoTags = otherPhotoCounts[friendId]
        email = None # FB won't give you the friends' emails

        if (primPhotoTags + otherPhotoTags > 0):
            logger.debug("Friend %d has %d primary photo tags and %d other photo tags", friendId, primPhotoTags, otherPhotoTags)

        f = datastructs.FriendInfo(userId, friendId, rec['first_name'], rec['last_name'], email, rec['sex'], dateFromFb(rec['birthday_date']), city, state, primPhotoTags, otherPhotoTags, rec['mutual_friend_count'])
        friends.append(f)
    logger.debug("returning %d mocked friends for %d (%s)", len(friends), userId, tim.elapsedPr())
    return friends


def getUserFb(userId, token):
    """gets more info about primary user from FB

    """
    fql = FQL_USER_INFO % (userId)
    url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=%s' % token

    # mock response from FB API
    responseJson = {'data' : [fakeUserInfo(userId)] }
    rec = responseJson['data'][0]
    city = rec['current_location'].get('city') if (rec.get('current_location') is not None) else None
    state = rec['current_location'].get('state') if (rec.get('current_location') is not None) else None
    email = rec.get('email')
    user = datastructs.UserInfo(rec['uid'], rec['first_name'], rec['last_name'], email, rec['sex'], dateFromFb(rec['birthday_date']),
                                city, state)
    return user

def getFriendEdgesFb(userId, tok, requireIncoming=False, requireOutgoing=False, skipFriends=None):
    """retrieves user's FB stream and calcs edges b/w user and her friends.

    makes multiple calls to FB! separate calcs & FB calls
    """
    if requireOutgoing:
        raise NotImplementedError("Stream reading not available for mock facebook module")

    skipFriends = skipFriends if skipFriends is not None else set()

    logger.debug("mocking getting friend edges from FB for %d", userId)
    tim = datastructs.Timer()
    friends = getFriendsFb(userId, tok)
    logger.debug("mocked getting %d friends total", len(friends))

    friendQueue = [f for f in friends if f.id not in skipFriends]
    friendQueue.sort(key=lambda x: x.mutuals, reverse=True)

    # Facebook limits us to 600 calls in 600 seconds, so we need to throttle ourselves
    # relative to the number of calls we're making (the number of chunks) to 1 call / sec.
    friendSecs = settings.STREAM_DAYS_OUT / settings.STREAM_DAYS_CHUNK_OUT

    edges = []
    user = getUserFb(userId, tok)
    for i, friend in enumerate(friendQueue):

        kwargs = {}
        if requireIncoming:
            kwargs = {
                'postLikes': random.randint(0, 50),
                'postComms': random.randint(0, 50),
                'statLikes': random.randint(0, 50),
                'statComms': random.randint(0, 50),
                'wallPosts': random.randint(0, 50),
                'wallComms': random.randint(0, 50),
                'tags': random.randint(0, 50),
            }

        ecIn = datastructs.EdgeCounts(
            friend.id,
            user.id,
            photoTarg=friend.primPhotoTags,
            photoOth=friend.otherPhotoTags,
            muts=friend.mutuals,
            **kwargs
        )
        e = datastructs.Edge(user, friend, ecIn, None)

        edges.append(e)
        logger.debug('friend %s', str(e.secondary))
        logger.debug('edge %s', str(e))  # zzz Edge class no longer has a __str__() method...
                                         #     not important enough to fix for mayors, but maybe should one day?

    logger.debug("mocked getting %d friend edges for %d (%s)", len(edges), userId, tim.elapsedPr())
    return edges
