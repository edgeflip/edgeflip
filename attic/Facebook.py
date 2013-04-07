#!/usr/bin/python
import sys
import urllib2
import urllib
import urlparse
import signal
import json
import re
import random
from calendar import timegm
import Utils
import time



# Facebook secrets
FB_ID = '111399285589490'
FB_SECRET = 'ca819150ad771e5cbcacf60bd88c04d7'
FB_TOKEN = '111399285589490|ChvF9GrYd2K9cHq07NQmcSVhDsc'

FB_TIMEOUT_SECS = 60
FB_MAX_BATCH_SIZE = 50

# fields we ask fb to give us when we request user info
FB_USER_FIELDS_GRAPH = 'id,name,first_name,middle_name,last_name,name,gender,locale,languages,link,username,third_party_id,timezone,updated_time,verified,bio,birthday,education,email,hometown,interested_in,location,political,favorite_athletes,favorite_teams,quotes,relationship_status,religion,significant_other,video_upload_limits,website,work'
FB_USER_FIELDS_FQL = 'uid,username,first_name,middle_name,last_name,name,affiliations,timezone,religion,birthday,birthday_date,sex,hometown_location,meeting_sex,meeting_for,relationship_status,significant_other_id,political,current_location,activities,interests,is_app_user,music,tv,movies,books,quotes,about_me,notes_count,wall_count,status,online_presence,locale,proxied_email,profile_url,allowed_restrictions,verified,profile_blurb,family,website,is_blocked,contact_email,email,third_party_id,name_format,video_upload_limits,games,is_minor,work,education,sports,favorite_athletes,favorite_teams,inspirational_people,languages,likes_count,friend_count,mutual_friend_count,can_post'


def getAccessToken(fbId=None, fbSecret=None):
    '''Returns the access token corresponding to a given app id and app secret'''
    if (fbId is None):
        fbId = FB_ID
    if (fbSecret is None):
        fbSecret = FB_SECRET
    oauth = 'https://graph.facebook.com/oauth/access_token?client_id=%s&client_secret=%s&grant_type=client_credentials' % (fbId, fbSecret)
    responseFile = urlopenTimeout(oauth)
    return responseFile.read().replace('access_token=', '')


class FacebookTimeoutException(Exception):
    pass
class FacebookBatchSizeException(Exception):
    pass

# See: http://docs.python.org/library/signal.html#example
def timeoutHandler(signum, frame):
    raise FacebookTimeoutException("Timeout opening FB url")

def urlopenTimeout(url, timeout=None):
    '''Performs a url open op with a signal timeout to avoid hanging processes'''
    if (timeout is None):
        timeout = FB_TIMEOUT_SECS
    signal.signal(signal.SIGALRM, timeoutHandler)  # set the signal handler
    signal.alarm(timeout)                            # set alarm
    responseFile = urllib2.urlopen(url)                       # may hang indefinitely
    signal.alarm(0)                          # disable the alarm
    return responseFile

def urlopenTimeoutRetry(url, timeout=None, tries=1):
    for attempt in range(1, tries + 1):
        try:
            return urlopenTimeout(url, timeout=timeout)
        except:
            nextAct = "retrying" if (attempt < tries) else "bailing"
            sys.stderr.write("ERROR opening url '%s' (attempt %d/%d, %s): %s\n" % (url, attempt, tries, nextAct, str(sys.exc_info()[0])))
            if (attempt >= tries):
                raise


def getFriendsBatch(userIds, token, timeout=None):
    '''Get friends for a bunch of users at a time.  Returns a dict user -> [ (fid1, fname1), (fid2, fname2), ... ] with
    None instead of a list in the case of a 400 (this may happen when user is not logged on, need to investigate zzz)'''
    if (len(userIds) > FB_MAX_BATCH_SIZE):
        raise FacebookBatchSizeException("batch requests have limit %d" % FB_MAX_BATCH_SIZE)

    # '[{"method":"GET","relative_url":"me"}, {"method":"GET","relative_url":"me/friends?limit=50"}]';
    requests = []
    for userId in userIds:
        requests.append('{"method":"GET","relative_url":"%s/friends?limit=9999"}' % userId)
    batchJson = urllib.quote('[' + ", ".join(requests) + ']')

    postUrl = "https://graph.facebook.com/?batch=" + batchJson + "&access_token=" + token + "&method=post"
    #sys.stderr.write("batch request url for %d users: %s\n" % (len(userIds), postUrl))


    #signal.signal(signal.SIGALRM, timeoutHandler) # set the signal handler and alarm
    #signal.alarm(FB_TIMEOUT_SECS)
    #responseFile = urllib2.urlopen(postUrl) #  may hang indefinitely
    #signal.alarm(0)          # disable the alarm
    responseFile = urlopenTimeout(postUrl, timeout=timeout)

    responses = json.load(responseFile)
    #sys.stderr.write("%d responses:\n\t%s\n" % (len(responses), str(responses)))

    user_friends = {}
    goodCount = 0
    for i, response in enumerate(responses):
        userId = userIds[i]
        # sys.stderr.write("response %d:\n\tcode: %s\n\theaders: %s\n\tbody: %s\n\n" % (i, response['code'], response['headers'], response['body']))
        #sys.stderr.write("response %d:\n\n" % (i))
        #sys.stderr.write("\t%s\n" % (str(response)[:200]))
        #sys.stderr.write("\tcode: %s\n" % (response['code']))

        #if (int(response['code']) == 200):
        if (response is not None) and (int(response['code']) == 200): #zzz for some reason, some responses are coming back None
            friendsJson = json.loads(response['body'])
            #paging = friendsJson['paging']
            #sys.stderr.write("\tpaging: %s\n" % (paging))
            friends = friendsJson['data']
            #sys.stderr.write("\t\t%s\n" % (friends))
            #sys.stderr.write("\tgot %d friends\n" % (len(friends)))
            user_friends[userId] = []
            for friend in friends:
                #sys.stderr.write("\t\t%s\t%s\n" % (friend['id'], friend['name']))
                fid = friend['id']
                fname = friend['name'] if ('name' in friend) else None
                user_friends[userId].append((int(fid), fname))
            goodCount += 1
        else:
            #sys.stderr.write(response['body'] + "\n")
            user_friends[userId] = None

    return user_friends



#http://www.facebook.com/people/Vicky-Tucker/100000702861373
def getUserInfo(userId, token, timeout=None):
    url = 'https://graph.facebook.com/%s?access_token=%s&fields=%s' % (userId, token, FB_USER_FIELDS_GRAPH)
    sys.stderr.write(url + "\n")
    responseFile = urlopenTimeout(url, timeout=timeout)
    responses = json.load(responseFile)
    #sys.stderr.write(str(responses))
    return responses


def getUserInfoFqlMulti(userIds, token, timeout=None, fieldsStr=None):
    if (fieldsStr is None):
        fieldsStr = FB_USER_FIELDS_FQL
    fqls = dict([ (userId, "SELECT %s FROM user WHERE uid=%s" % (fieldsStr, userId)) for userId in userIds ])
    url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(str(fqls)) + '&format=json&access_token=' + token

    #sys.stderr.write(url + "\n")
    responseFile = urlopenTimeout(url, timeout=timeout)
    responses = json.load(responseFile)
    userId_attrDict = {}
    for entry in responses['data']:
        #sys.stderr.write("user %s, info %s\n\n" % (entry['name'], entry['fql_result_set']))
        userId = str(entry['name'])
        attrDict = entry['fql_result_set'][0] if (entry['fql_result_set']) else None
        userId_attrDict[userId] = attrDict
    return userId_attrDict

def getUserLikesFqlMulti(userIds, token, timeout=None):
    fqls = dict([ (userId, "SELECT %s FROM user WHERE uid=%s" % (fieldsStr, userId)) for userId in userIds ])
    url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(str(fqls)) + '&format=json&access_token=' + token

    #sys.stderr.write(url + "\n")
    responseFile = urlopenTimeout(url, timeout=timeout)
    responses = json.load(responseFile)
    userId_attrDict = {}
    for entry in responses['data']:
        #sys.stderr.write("user %s, info %s\n\n" % (entry['name'], entry['fql_result_set']))
        userId = str(entry['name'])
        attrDict = entry['fql_result_set'][0] if (entry['fql_result_set']) else None
        userId_attrDict[userId] = attrDict
    return userId_attrDict





def getSuiInfoFqlMulti(userIds, token, timeout, fieldsStr):
    fqls = dict([ (userId, "SELECT %s FROM standard_user_info WHERE uid=%s" % (fieldsStr, userId)) for userId in userIds ])
    url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(str(fqls)) + '&format=json&access_token=' + token
    #sys.stderr.write(url + "\n")
    responseFile = urlopenTimeout(url, timeout=timeout)
    responses = json.load(responseFile)
    userId_attrDict = {}
    for entry in responses['data']:
        #sys.stderr.write("user %s, info %s\n\n" % (entry['name'], entry['fql_result_set']))
        userId = str(entry['name'])
        attrDict = entry['fql_result_set'][0] if (entry['fql_result_set']) else None
        userId_attrDict[userId] = attrDict
    return userId_attrDict




def getUserBirthday(userId, token, timeout=None):
    sys.stderr.write("grabbing birthday for user: '%s'\n" % userId)

    url = "https://graph.facebook.com/%s?fields=birthday&access_token=%s" % (userId, token)
    sys.stderr.write("graph API url: %s\n" % url)
    responseFile = urlopenTimeout(url, timeout=timeout)
    responses = json.load(responseFile)
    sys.stderr.write("graph API resp: %s\n\n" % str(responses))

    url = "https://graph.facebook.com/fql?q="
    url += urllib.quote_plus("SELECT uid, birthday FROM standard_user_info WHERE uid=" + str(userId))
    url += '&format=json&access_token=' + token
    sys.stderr.write("fql (standard_user_info) url: %s\n" % url)
    try:
        responseFile = urlopenTimeout(url, timeout=timeout)
        responses = json.load(responseFile)
        sys.stderr.write("fql (standard_user_info) resp: %s\n\n" % str(responses))
    except urllib2.HTTPError:
        sys.stderr.write("error\n")

    url = "https://graph.facebook.com/fql?q="
    url += urllib.quote_plus("SELECT uid, birthday, birthday_date FROM user WHERE uid=" + str(userId))
    url += '&format=json&access_token=' + token
    sys.stderr.write("fql (user) url: %s\n" % url)
    responseFile = urlopenTimeout(url, timeout=timeout)
    responses = json.load(responseFile)
    sys.stderr.write("fql (user) resp: %s\n\n" % str(responses))

    sys.stderr.write("\n\n")

    return responses


def getFriendsRanked(userId, token, feedLimit=1000, timeout=None):
    friend_feed = getFriendsFeedCounts(userId, token, limit=feedLimit, timeout=timeout)
    friend_muts = getFriendsMutualCounts(userId, token, timeout=timeout)

    for friend, muts in friend_muts.items():
        if (muts is None):
            sys.stderr.write("bad muts: %s, %s\n" % (friend, muts))
            raise

    friends = set(friend_feed.keys() + friend_muts.keys())
    friendTups = [ (friend[0], friend[1], friend_feed.get(friend, 0), friend_muts.get(friend, 0)) for friend in friends ]

    # rank by feed
    sys.stderr.write("\n\n")
    for i, (fid, fname, ffeed, fmuts) in enumerate(sorted(friendTups, key=lambda x: x[2], reverse=True)[:20]):
        sys.stderr.write("%d. %30s\t%s\t%s\n" % (i, fname, ffeed, fmuts))

    # rank by muts
    sys.stderr.write("\n\n")
    for i, (fid, fname, ffeed, fmuts) in enumerate(sorted(friendTups, key=lambda x: x[3], reverse=True)[:20]):
        sys.stderr.write("%d. %30s\t%s\t%s\n" % (i, fname, ffeed, fmuts))

    # rank by harmonic(feed, muts)
    sys.stderr.write("\n\n")
    friendTupsPP = [ tuple(list(tup) + [harmonic(tup[2], tup[3])]) for tup in friendTups ]
    for i, (fid, fname, ffeed, fmuts, harm) in enumerate(sorted(friendTupsPP, key=lambda x: x[4], reverse=True)[:20]):
        sys.stderr.write("%d. %30s\t%s\t%s\t%.2f\n" % (i, fname, ffeed, fmuts, harm))

    # rank by geometric(feed, muts)
    sys.stderr.write("\n\n")
    friendTupsPP = [ tuple(list(tup) + [math.sqrt(tup[2]*tup[3])]) for tup in friendTups ]
    for i, (fid, fname, ffeed, fmuts, mean) in enumerate(sorted(friendTupsPP, key=lambda x: x[4], reverse=True)[:20]):
        sys.stderr.write("%d. %30s\t%s\t%s\t%.2f\n" % (i, fname, ffeed, fmuts, mean))





def stripLongestPrefix(s, prefixes):
    for prefix in sorted(prefixes, key=len, reverse=True):
        if (s.startswith(prefix)):
            return s[len(prefix):]
    return s

def batchifiedUrl(urls, token, limit=10000):
    relativeUrls = [ stripLongestPrefix(u, ["https://graph.facebook.com/", "graph.facebook.com/", "/"]) for u in urls ]
    # '[{"method":"GET","relative_url":"me"}, {"method":"GET","relative_url":"me/friends?limit=50"}]';
    requests = [ '{"method":"GET","relative_url":"%s"}' % (relUrl) for relUrl in relativeUrls ]
    requestsStr = urllib.quote_plus('[' + ", ".join(requests) + ']')
    batchUrl = "https://graph.facebook.com/?batch=" + requestsStr + "&access_token=" + token + "&method=post&limit=" + str(limit)
    return batchUrl

#def batchRequest(urls, token, timeout=None):
#             '''Returns a list of (code, json/message) tuples for request urls'''
#             if (len(urls) > FB_MAX_BATCH_SIZE):
#                 raise FacebookBatchSizeException("batch requests have limit %d" % FB_MAX_BATCH_SIZE)
#             batchUrl = batchifiedUrl(urls, token)
#             responsesFile = urlopenTimeout(batchUrl, timeout=timeout)
#             responses = []
#             responsesRaw = json.load(responsesFile)
#             goodCount = 0
#             badCount = 0
#             noneCount = 0
#             for i, responseRaw in enumerate(responsesRaw):
#                 if (responseRaw is not None):
#                     code = int(responseRaw['code'])
#                     body = responseRaw['body']
#                     if (code == 200):
#                         body = json.loads(body)
#                         goodCount += 1
#                     else:
#                         badCount += 1
#                     responses.append((code, body))
#                 else:
#                     responses.append((None, None))
#                     noneCount += 1
#             #sys.stderr.write("batch request got %d good, %d bad, %d none\n" % (goodCount, badCount, noneCount))
#             return responses

def batchRequest(fbIds, urlSuff, token, limit=100000, timeout=None):
    '''Returns a dict of fbId -> (code, json/message) tuples for request ids and stub url'''
    if (len(fbIds) > FB_MAX_BATCH_SIZE):
        raise FacebookBatchSizeException("batch requests have limit %d" % FB_MAX_BATCH_SIZE)
    if (token is None):
        token = getAccessToken()

    urls = [ str(i) + urlSuff for i in fbIds ]
    #sys.stderr.write("urls: \n" + "\n".join(urls) + "\n")
    batchUrl = batchifiedUrl(urls, token, limit)
    #sys.stderr.write("batch url:\n" + urllib.unquote_plus(batchUrl) + "\n")

    responsesFile = urlopenTimeout(batchUrl, timeout=timeout)

    responsesRaw = json.load(responsesFile)
    responses = {} # fbid -> (code, body)
    for fbid, responseRaw in zip(fbIds, responsesRaw):
        if (responseRaw is not None) and (int(responseRaw['code']) == 200):
            responses[fbid] = json.loads(responseRaw['body'])
        else:
            responses[fbid] = None
    return responses


def getUserInfoBatch(userIds, token=None, timeout=None, fieldsStr=None):
    if (fieldsStr is None):
        fieldsStr = FB_USER_FIELDS_GRAPH
    # email     vickyit@live.com
    # first_name          Vicky
    # gender                  female
    # id             100000702861373
    # last_name           Tucker
    # link         http://www.facebook.com/people/Vicky-Tucker/100000702861373
    # locale     en_US
    # location                {u'id': u'110810538938998', u'name': u'Cheektowaga, New York'}
    # name    Vicky Tucker
    # third_party_id               Y-4_ifS96Pi4sVdx5kaOrZ5Q5jU
    return batchRequest(userIds, "?fields=" + fieldsStr, token, timeout)


# userIds = [1219551338, 45011293]
def getUserLikesBatch(userIds, token=None, timeout=None):
    #relUrls = [ "%s/likes?" % (userId) for userId in userIds ]
    #responseTups = batchRequest(relUrls, token, timeout)

    #{
    #   "data": [
    #               {
    #      "name": "Data Without Borders",
    #      "category": "Non-profit organization",
    #      "id": "246858321996099",
    #      "created_time": "2011-07-01T18:52:19+0000"
    #               },
    #               {
    #      "name": "The Chicago Council on Science & Technology",
    #      "category": "Local business",
    #      "id": "163815626997995",
    #      "created_time": "2011-01-13T17:20:30+0000"
    #               },
    #               {
    #      "name": "PenTales",
    #      "category": "Society/culture",
    #      "id": "197277513951",
    #      "created_time": "2010-11-23T22:31:04+0000"
    #               }
    #             ]
    #}
    responses = batchRequest(userIds, "/likes?", token, timeout)
    user_data = {}
    for user, data in responses.items():
        if (data is not None):
            sys.stderr.write("user %s likes\n" % (user))
            for thing in data['data']:
                sys.stderr.write("\tthing %s\n" % str(thing))

            tups = [ (attrDict['id'], attrDict['name'], attrDict['category'], attrDict.get('created_time', None)) for attrDict in data['data'] ]
            user_data[user] = tups
        else:
            user_data[user] = None
    return user_data


def getPageInfosBatch(pageIds, token=None, timeout=None):
    return batchRequest(pageIds, "?fields=id,name,category,website,likes,talking_about_count", token, timeout)




def getPagePostsBatch(pageIds, token=None, timeout=None, postType='posts'):
    responses = batchRequest(pageIds, "/" + postType + "?", token, timeout)
    #{
    #   "data": [
    #      {
    #         "id": "189592294391890_276526335769630",
    #         "from": {
    #            "name": "Dogs Against Romney",
    #            "category": "Personal website",
    #            "id": "189592294391890"
    #         },
    #         "message": "Re-posting one of the great member submissions. Go Wooten! #irideinside",
    #         "link": "http://www.facebook.com/photo.php?fbid=3258749038134&set=o.189592294391890&type=1",
    #         "caption": "Wooten knows Mitt is Mean!!",
    #         "properties": [
    #            {
    #               "name": "By",
    #               "text": "Melissa McDougald Odom"
    #            }
    #         ],
    #         "icon": "http://static.ak.fbcdn.net/rsrc.php/v1/yD/r/aS8ecmYRys0.gif",
    #         "type": "photo",
    #         "object_id": "3258749038134",
    #         "application": {
    #            "name": "Photos",
    #            "id": "2305272732"
    #         },
    #         "created_time": "2012-04-17T19:53:48+0000",
    #         "updated_time": "2012-04-17T20:03:23+0000",
    #         "shares": {
    #            "count": 28
    #         },
    #         "likes": {
    #            "data": [
    #               {
    #      "name": "Patti Pelz",
    #      "id": "1669576560"
    #               },
    #               {
    #      "name": "Carol Nolan",
    #      "id": "1777440480"
    #               },
    #               {
    #      "name": "Amy Yerdon",
    #      "id": "680847753"
    #               },
    #               {
    #      "name": "Ed Violette",
    #      "id": "1803151727"
    #               }
    #            ],
    #            "count": 112
    #         },
    #         "comments": {
    #            "data": [
    #               {
    #      "id": "189592294391890_276526335769630_1534884",
    #      "from": {
    #         "name": "Nonya Flippin Bizz",
    #         "id": "100000692892804"
    #      },
    #      "message": "Halp, I've got a tail hole on my head! I'm sure sweet Wooten got an extra special treat for that :)",
    #      "created_time": "2012-04-17T20:01:46+0000"
    #               },
    #               {
    #      "id": "189592294391890_276526335769630_1534891",
    #      "from": {
    #         "name": "Raymond Gross",
    #         "id": "555565115"
    #      },
    #      "message": "Speaking of being cruel to animals---Let's not forget how cruel Mitt Romney was to his dog and how much Newt Gingrich loves animals. I know of many folks who voted for Mitt, including the MS Governor, Lt. Governor and Sec. of State, that probably failed to do their vetting homework. And many others who voted for Rick Santorum are now wishing they had voted for Newt Gingrich. Yeap, old Rick and Mitt sure pulled wool over a lot of folks eyes in Tenn, Ala, Miss and La. Hopefully and prayerfully the folks in NC, Penn. Delaware, Conn . and the other remaining States will support the only proven conservative, Newt Gingrich, in order for us to take back our Country, in spite of those who betrayed Mr. Newt in the South.",
    #      "created_time": "2012-04-17T20:03:23+0000"
    #               }
    #            ],
    #            "count": 10
    #         }
    #      },
    user_data = {}
    for fbId, data in responses:
        postTups = []
        if (data is not None):
            for postDict in data['data']:
                postId = postDict['id']
                fromId = postDict['from']['id']
                postType = postDict.get('type', None)
                created = postDict.get('created_time', None)
                updated = postDict.get('updated_time', None)
                likes = postDict['likes']['count']
                comments = postDict['comments']['count']
                link = postDict.get('link', None)
                postTups.append((fbId, postId, fromId, postType, link, likes, comments, created, updated))
        user_data[fbId] = postTups
    return user_data





def getUserConns(userId, token, timeout=None, conns=None):
    if (conns is None):
        conns = ['accounts', 'achievements', 'activities', 'albums', 'apprequests', 'books', 'checkins', 'events', 'family', 'feed', 'friendlists', 'friendrequests', 'friends', 'games', 'groups', 'home', 'inbox', 'interests', 'likes', 'links', 'movies', 'music', 'mutualfriends', 'notes', 'notifications', 'outbox', 'payments', 'permissions', 'photos', 'picture', 'pokes', 'posts', 'questions', 'scores', 'statuses', 'tagged', 'television', 'updates', 'videos']
    for i, conn in enumerate(conns):
        url = 'https://graph.facebook.com/%s/%s?access_token=%s' % (userId, conn, token)
        sys.stderr.write("%d/%d checking %s for user %s\t%s\n" % (i, len(conns)-1, conn, userId, url))
        try:
            responseFile = urlopenTimeout(url, timeout=timeout)
        except urllib2.HTTPError:
            sys.stderr.write("\tbad request\n")
            continue
        except FacebookTimeoutException:
            sys.stderr.write("\trequest timeout\n")
            continue

        responseStr = responseFile.read()
        try:
            responseJson = json.loads(responseStr)
            sys.stderr.write(str(responseJson) + "\n\n")
            if (responseJson['data']):
                sys.stderr.write("\t%s:\n" % conn)
                for obj in responseJson['data']:
                    sys.stderr.write("\t\t%s\n" % (str(obj)))
                sys.stderr.write("\n")

        except ValueError:
            sys.stderr.write("\t\tno json\n")

def getUserFriends(userId, token, checkUser=False):
    friends = getFriendsBatch([userId], token)[userId]
    #sys.stderr.write("friends: %s\n" % str(friends))
    if (checkUser):
        friend_user = {}
        for friend, attrDict in getUserInfoFqlMulti(friends, token, fieldsStr="uid,is_app_user").items():
            friend_user[friend] = attrDict['is_app_user']
        return friend_user
    else:
        return friends



# completely heuristic, based on commonly found words in political field
# and returns 'left', 'right', 'center', 'unknown', or 'other'
searchKeysDefault = {}
for key in ['democrat', 'liberal', 'obama', 'progressive', 'left', 'socialist', 'obama', 'green']:
    searchKeysDefault[key] = 'left'
for key in ['conservat', 'republic', 'libert', 'right', 'tea']:
    searchKeysDefault[key] = 'right'
for key in ['moderat', 'center', 'independ', 'middle']:
    searchKeysDefault[key] = 'center'

def transformPolitical(political, searchKeys=None, verbose=False):
    if (searchKeys is None):
        searchKeys = searchKeysDefault
    matches = set([ pol for key, pol in searchKeys.items() if (political.lower().find(key) > -1) ])
    if (len(matches) == 0):
        ret = "unknown"
    elif (len(matches) == 1):
        ret = matches.pop()
    else:
        ret = "other"
    if (verbose):
        sys.stderr.write("'%s' -> %s\n" % (political, ret))
    return ret





# {u'city': u'Somerset', u'name': u'Somerset, Kentucky', u'zip': u'', u'country': u'United States', u'state': u'Kentucky', u'id': 112674218747903}
def parseLocationJson(locJsonStr, retNone=''):
    #sys.stderr.write("parsing '%s'\n" % locJsonStr)

#             locJsonStr = re.sub(r"{\s*'?(\w)", r'{"\1', locJsonStr)
#             locJsonStr = re.sub(r",\s*'?(\w)", r',"\1', locJsonStr)
#             locJsonStr = re.sub(r"(\w)'?\s*:", r'\1":', locJsonStr)
#             locJsonStr = re.sub(r":\s*'(\w)'\s*([,}])", r':"\1"\2', locJsonStr)

#             locJsonStr = locJsonStr.decode("string-escape")
#             locJsonStr = Utils.removeNonAscii(locJsonStr)
#             locJsonStr = locJsonStr.replace("u'", '"')
#             locJsonStr = locJsonStr.replace("':", '":')
#             locJsonStr = locJsonStr.replace("',", '",')
#             locJsonStr = locJsonStr.replace("'}", '"}')

#             sys.stderr.write("parsing '%s'\n" % locJsonStr)

#             locJson = json.loads(locJsonStr)
#             city = locJson.get('city', "")
#             state = Utils.state_abbrev.get(locJson.get('state', ""), "")
#             zzip = locJson.get('zip', "")


    # screw it, parse it by hand...
    city = retNone
    state = retNone
    zzip = retNone
    locJsonStr = locJsonStr[2:-1] # get rid of brackets and lead u
    if (locJsonStr != 'None') and (locJsonStr != ''):
        for pairStr in locJsonStr.split(', u'):
            #sys.stderr.write("\tparsing '%s'\n" % pairStr)
            if (pairStr.startswith("'id'")):
                continue
            k, v = pairStr.split(': u')
            k = k[1:-1]
            v = v[1:-1]
            if (k == 'city'):
                city = v
            elif (k == 'state'):
                state = Utils.state_abbrev.get(v, "")
            elif (k == 'zip'):
                zzip = v
    #sys.stderr.write("parsed %s -> %s, %s, %s\n" % (locJsonStr, city, state, zzip))
    return (city, state, zzip)


def parseBirthday(bdayStr, retNone=''):
    byear = retNone
    bmonth = retNone
    bdate = retNone
    if (bdayStr == 'None') or (bdayStr == '00/00/0000') or (bdayStr == ''):
        return (retNone, retNone, retNone)
    else:
        if (bdayStr.find(', ') == -1): # month date
            bmonth, bdate = bdayStr.split()
        else:
            bmonth, bdate, byear = bdayStr.split()
            bdate = bdate.rstrip(',')
        return (byear, bmonth, bdate)


def addParsedLocationColumns(colNum, infileName=None, outfileName=None, header=False):
    infile = sys.stdin if (infileName is None) else open(infileName, 'r')
    outfile = sys.stdout if (outfileName is None) else open(outfileName, 'w')

    if (header):
        outfile.write(infile.readline()[:-1] + "\tcity\tstate\tzip\n")

    for line in infile:
        elts = line[:-1].split('\t')
        locStr = elts[colNum]
        if (locStr == 'None'):
            city, state, zzip == "", "", ""
        else:
            city, state, zzip = parseLocationJson(locStr)
        lineNew = "\t".join([line[:-1], city, state, zzip]) + "\n"
        outfile.write(lineNew)



def parseTitles(colNameId, colNameField, infileName=None, outfileName=None, header=None, delimCol='\t', delimField=', ', append=False):
    '''Writes out uid, title, titleStop for each user-title combo it parses out'''
    from nltk.corpus import stopwords
    stops = set(stopwords.words('english'))
    infile = sys.stdin if (infileName is None) else open(infileName, 'r')
    outfile = sys.stdout if (outfileName is None) else open(outfileName, 'a' if (append) else 'w')

    if (header is None):
        colNames = infile.readline().rstrip("\n").split(delimCol)
    else:
        colNames = header
    colIdxName = colNames.index(colNameId)
    colIdxField = colNames.index(colNameField)
    lineCount = 0
    userCount = 0
    titCount = 0
    for line in infile:
        lineCount += 1
        if (lineCount % 100000 == 0): sys.stderr.write("\t%d\n" % lineCount)
        elts = line.rstrip("\n").split(delimCol)
        uid = elts[colIdxName]
        field = elts[colIdxField]
        if (field):
            userCount += 1
            titles = field.split(delimField)
            for title in titles:
                titCount += 1
                titleFilt = " ".join([ w for w in title.lower().split() if not w in stops ])
                outfile.write("%s%s%s%s%s\n" % (uid, delimCol, title, delimCol, titleFilt))
    sys.stderr.write("parsed %d lines for %s, wrote %d titles for %d users\n" % (lineCount, colNameField, titCount, userCount))

    return lineCount

def getColumnM(col, infileNames, outfileName, delim='\t'):
    #sys.stderr.write(str(infileNames) + " -> " + str(outfileName) + "\n")
    lineCount = 0
    for i, infileName in enumerate(infileNames):
        sys.stderr.write("%d/%d %s:\n" % (i, len(infileNames) - 1, infileName))
        lineCount += getColumn(col, infileName, outfileName, delim, append=True)
        sys.stderr.write("\n")
    return lineCount
