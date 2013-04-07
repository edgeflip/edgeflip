#!/usr/bin/python
import sys
import urlparse
import urllib
import json
import time
import itertools
from joblib import Parallel, delayed
import Facebook


MAX_ATTEMPTS = 10 # number of times we let each api call fail before giving up
BATCH_SIZE = 40 # number of queries to batch together at a time


# handles paging for a single source
def getDataPaging(url, limit=1000000, timeout=None, multiplePages=True):
    parsed = urlparse.urlparse(url) # scheme://netloc/path;parameters?query#fragment.
    args = urlparse.parse_qs(parsed.query)
    # sys.stderr.write("args: %s\n" % args)
    args['limit'] = limit # replace what's there if it exists
    urlStart = urlparse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urllib.urlencode(args, doseq=True), parsed.fragment))
    # sys.stderr.write("url: %s\n" % url)
    url = urlStart
    datas = []
    while (url is not None) and (len(datas) < limit):
        sys.stderr.write("\thave %d\tnext url: %s\n" % (len(datas), shortenToken(url)))

        for attempt in range(MAX_ATTEMPTS ):
            response = None
            try:
                response = json.load(Facebook.urlopenTimeout(url, timeout=timeout))
            except:
                sys.stderr.write("ERROR with request (attempt %d): %s\n" % (attempt, str(sys.exc_info()[1])))
                if (response is not None):
                    sys.stderr.write("\t have data: '%s'\n" % (str(response)))
                continue
            else: # we were successful
                break
        else: # we failed all attempts
            raise

        if (response['data']):
            datas.extend(response['data'])
            if (multiplePages):
                url = response['paging'].get('next', None) if ('paging' in response) else None
            else:
                url = None
        else:
            url = None
    return datas[:limit]

def getGraphConns(fbId, graphConn, token, fields=None, limit=1000000, timeout=None, paging=True):
    url = "https://graph.facebook.com/%s/%s?access_token=%s" % (fbId, graphConn, token)
    if (fields is not None):
        url += "&fields=%s" % fields

    sys.stderr.write("\turl: " + url + "\n")

    datas = getDataPaging(url, limit, timeout, multiplePages=paging)
    sys.stderr.write("\tgot %d %s for %s\n" % (min(len(datas), limit), graphConn, fbId))
    return datas


def getGraphInfoBatch(thingIds, token, fields=None, timeout=None):
    thingId_info = {}
    for start in range(0, len(thingIds), BATCH_SIZE):
        #sys.stderr.write("\tgrabbing batch %d-%d of %d\n" % (start, start + BATCH_SIZE, len(thingIds)))
        thingIdsChunk = thingIds[start:start+BATCH_SIZE]
        urlSuff = "/?"
        if (fields is not None):
            urlSuff += "&fields=%s" % fields
        for attempt in range(MAX_ATTEMPTS ):
            thingId_response = None
            try:
                thingId_response = Facebook.batchRequest(thingIdsChunk, urlSuff, token, timeout=timeout)
                noneCount = 0                
                for thingId, response in thingId_response.items():
                    #sys.stderr.write("thingId: %s\tresponse: %s\n" % (thingId, response))
                    if (response is not None):
                        thingId_info[thingId] = response
                    else:
                        #sys.stderr.write("ERROR None in batch responses: %s -> %s\n" % (thingId, str(response)))
                        noneCount += 1                    
                if (noneCount):
                    sys.stderr.write("ERROR None in batch responses (%d/%d)\n" % (noneCount, len(thingId_response)))

            except:
                sys.stderr.write("ERROR with batch request (attempt %d): %s\n" % (attempt, str(sys.exc_info()[1])))
                if (thingId_response is not None):
                    sys.stderr.write("\t have data: '%s'\n" % (str(thingId_response)[:1000]))
                continue
            else: # we were successful
                break
        else: # we failed all attempts
            raise
    return thingId_info


def getGraphConnsBatch(thingIds, graphConn, token, filtFunc=lambda x: True, fields=None, limit=100000, timeout=None):
    thingId_data = {}
    for start in range(0, len(thingIds), BATCH_SIZE):
        sys.stderr.write("\tgrabbing batch %d-%d of %d\n" % (start, start + BATCH_SIZE, len(thingIds)))
        thingIdsChunk = thingIds[start:start+BATCH_SIZE]
        urlSuff = "/" + graphConn + "?limit=" + str(limit)
        if (fields is not None):
            urlSuff += "&fields=%s" % fields
        for attempt in range(MAX_ATTEMPTS ):
            thingId_response = None
            try:
                thingId_response = Facebook.batchRequest(thingIdsChunk, urlSuff, token, limit, timeout=timeout)
                for thingId, response in thingId_response.items():
                    sys.stderr.write("thingId: %s\tresponse: %s\n" % (thingId, response))
                    if (response is not None):
                        thingId_data[thingId] = filter(filtFunc, response)
                    else:
                        sys.stderr.write("ERROR None in batch responses: %s -> %s\n" % (thingId, str(response)))
            except:
                sys.stderr.write("ERROR with batch request (attempt %d): %s\n" % (attempt, str(sys.exc_info()[1])))
                if (thingId_response is not None):
                    sys.stderr.write("\t have data: '%s'\n" % (str(thingId_response)[:1000]))
                continue
            else: # we were successful
                break
        else: # we failed all attempts
            raise
    return thingId_data

def getGraphConnsBatchParallel(thingIds, graphConn, token, filtFunc=lambda x: True, numJobs=5, fields=None, limit=100000, timeout=None):
    thingIdsChunks = [ thingIds[start:start+BATCH_SIZE] for start in range(0, len(thingIds), BATCH_SIZE) ]
    responseDicts = Parallel(n_jobs=numJobs)(delayed(getGraphConnsBatch)(thingIdsChunk, graphConn, token, filtFunc) for thingIdsChunk in thingIdsChunks)
    thingId_data = {}
    for responseDict in responseDicts:
        for k, v in responseDict.items():
            thingId_data[k] = v
    return thingId_data


def classifyUrlsCgi(urls, numCats, whitelist=None, numJobs=3):
    labelScores = Parallel(n_jobs=numJobs)(delayed(classifyUrlCgi)(url, numCats, whitelist) for url in urls)
    sys.stderr.write("got len %d back\n" % len(labelScores))
    #sys.stderr.write("%s\n" % str(url_stuff))
    url_labelScores = dict(zip(urls, labelScores))
    return url_labelScores


    thingId_data = {}
    for start in range(0, len(thingIds), BATCH_SIZE):
        sys.stderr.write("\tgrabbing batch %d-%d of %d\n" % (start, start + BATCH_SIZE, len(thingIds)))
        thingIdsChunk = thingIds[start:start+BATCH_SIZE]
        urlSuff = "/" + graphConn + "?limit=" + str(limit)
        if (fields is not None):
            urlSuff += "&fields=%s" % fields
        for attempt in range(MAX_ATTEMPTS ):
            thingId_response = None
            try:
                thingId_response = Facebook.batchRequest(thingIdsChunk, urlSuff, token, limit, timeout=timeout)
                for thingId, response in thingId_response.items():
                    #sys.stderr.write("thingId: %s\tresponse: %s\n" % (thingId, response))
                    if (response is not None):
                        thingId_data[thingId] = response['data']
                    else:
                        sys.stderr.write("ERROR None in batch responses: %s -> %s\n" % (thingId, str(response)))
            except:
                sys.stderr.write("ERROR with batch request (attempt %d): %s\n" % (attempt, str(sys.exc_info()[1])))
                if (thingId_response is not None):
                    sys.stderr.write("\t have data: '%s'\n" % (str(thingId_response)[:1000]))
                continue
            else: # we were successful
                break
        else: # we failed all attempts
            raise
    return thingId_data





def getLikes(thing, doLookupToken=None):
    if ('likes' in thing):
        if (doLookupToken is not None):
            likersJson = getGraphConns(thing['id'], 'likes', doLookupToken, paging=True)
        else:
            likersJson = thing['likes']['data']
        sys.stderr.write("%s likes: count %s, data %d, lookup %d\n" % (thing['id'], thing['likes'].get('count', None), len(thing['likes'].get('data', [])), len(likersJson)))
        return [ FbUser(json['id'], json['name'], doLookupToken) for json in likersJson ]
    else:
        return []

def getComments(thing, doLookupToken=None):
    if ('comments' in thing):
        if (doLookupToken is not None):
            commentersJson = getGraphConns(thing['id'], 'comments', doLookupToken, paging=True)
        else:
            commentersJson = thing['comments']['data']
        sys.stderr.write("%s comments: count %s, data %d, lookup %d\n" % (thing['id'], thing['comments'].get('count', None), len(thing['comments'].get('data', [])), len(commentersJson)))
        return [ FbUser(json['from']['id'], json['from']['name'], doLookupToken) for json in commentersJson ]
    else:
        return []

def getLikesBatch(things, doLookupToken=None, verbose=False):
    if (doLookupToken is None):
        thingId_likersJson = dict([ (thing['id'], getLikes(thing, None)) for thing in things ])
    else:
        thingId_likersJson = getGraphConnsBatch([ thing['id'] for thing in things ], 'likes', doLookupToken)
    thingId_likers = {}
    for thingId, likersJson in thingId_likersJson.items():
        if (verbose):
            sys.stderr.write("\textracting likers from %s\n" % likersJson)
        thingId_likers[thingId] = [ FbUser(json['id'], json.get('name', ''), doLookupToken) for json in likersJson ]
    return thingId_likers

def getCommentsBatch(things, doLookupToken=None, verbose=False):
    if (doLookupToken is None):
        thingId_commentersJson = dict([ (thing['id'], getComms(thing, None)) for thing in things ])
    else:
        thingId_commentersJson = getGraphConnsBatch([ thing['id'] for thing in things ], 'comments', doLookupToken)
    thingId_commenters = {}
    for thingId, commentersJson in thingId_commentersJson.items():
        if (verbose):
            sys.stderr.write("\textracting commenters from %s\n" % commentersJson)
        thingId_commenters[thingId] = [ FbUser(json['from']['id'], json['from']['name'], doLookupToken) for json in commentersJson ]
    return thingId_commenters


def countPrimaryPostSecondLikes(posts, whitelist=None, doLookupToken=None, verbose=False):
    user_count = {}
    if (verbose):
        sys.stderr.write("finding likes for %d posts\n" % (len(posts)))
        sys.stderr.write("lookup token: %s\n" % (str(doLookupToken)))
        #sys.stderr.write("%s\n" % (str(posts)))
        #sys.stderr.write("\n")
    for t, thing in enumerate(posts):
        if (verbose):
            sys.stderr.write("getting likes for thing %d/%d: %s\n" % (t, len(posts), str(thing)))
        likers = getLikes(thing, doLookupToken=doLookupToken)
        if (verbose):
            sys.stderr.write("got %d likers\n\n" % (len(likers)))
        for user in likers:
            user_count[user] = user_count.get(user, 0) + 1
    return user_count if (whitelist is None) else filterByKeys(user_count, whitelist)

def countPrimaryPostSecondComms(posts, whitelist=None, doLookupToken=None, verbose=False):
    user_count = {}
    if (verbose):
        sys.stderr.write("finding comments for %d posts\n" % (len(posts)))
        sys.stderr.write("lookup token: %s\n" % (str(doLookupToken)))
        #sys.stderr.write("%s\n" % (str(posts)))
        #sys.stderr.write("\n")
    for t, thing in enumerate(posts):
        if (verbose):
            sys.stderr.write("getting comments for thing %d/%d: %s\n" % (t, len(posts), str(thing)))
        commenters = getComments(thing, doLookupToken=doLookupToken)
        if (verbose):
            sys.stderr.write("got %d commenters\n\n" % (len(commenters)))
        for user in commenters:
            user_count[user] = user_count.get(user, 0) + 1
    return user_count if (whitelist is None) else filterByKeys(user_count, whitelist)

def countSecondPostPrimaryLikes(posts, primary, whitelist=None, doLookupToken=None, verbose=False):
    user_count = {}
    if (verbose):
        sys.stderr.write("finding likes by %s for %d posts\n" % (primary, len(posts)))
        sys.stderr.write("lookup token: %s\n" % (str(doLookupToken)))
        #sys.stderr.write("%s\n" % (str(posts)))
        sys.stderr.write("\n")
    #for t, thing in enumerate(posts):
    #    if (verbose):
    #        sys.stderr.write("getting likes for thing %d/%d: %s\n" % (t, len(posts), str(thing)))
    #    user = FbUser(thing['from']['id'], thing['from']['name'], doLookupToken)
    #    for liker in getLikes(thing, doLookupToken=doLookupToken):
    #        if (liker == primary):
    #            user_count[user] = user_count.get(user, 0) + 1
    #    if (verbose):
    #        sys.stderr.write("\n")
    postId_likers = getLikesBatch(posts, doLookupToken=doLookupToken)
    if (verbose):
        sys.stderr.write("\tfound %d secondary posts, %d total likers\n" % (len(posts), sum([ len(x) for x in postId_likers.values() ])))
    for post in posts:
        user = FbUser(post['from']['id'], post['from']['name'], doLookupToken)
        for liker in postId_likers.get(post['id'], []):
            if (liker == primary):
                user_count[user] = user_count.get(user, 0) + 1
    if (verbose):
        sys.stderr.write("\tprimary liked %d posts\n" % (sum(user_count.values())))
    return user_count if (whitelist is None) else filterByKeys(user_count, whitelist)

def countSecondPostPrimaryComms(posts, primary, whitelist=None, doLookupToken=None, verbose=False):
    user_count = {}
    if (verbose):
        sys.stderr.write("finding comments by %s for %d posts\n" % (primary, len(posts)))
        sys.stderr.write("lookup token: %s\n" % (str(doLookupToken)))
        #sys.stderr.write("%s\n" % (str(posts)))
        sys.stderr.write("\n")
    #for t, thing in enumerate(posts):
    #    if (verbose):
    #        sys.stderr.write("getting comments for thing %d/%d: %s\n" % (t, len(posts), str(thing)))
    #    user = FbUser(thing['from']['id'], thing['from']['name'], doLookupToken)
    #    for commenter in getComments(thing, doLookupToken=doLookupToken):
    #        if (commenter == primary):
    #            user_count[user] = user_count.get(user, 0) + 1
    #    if (verbose):
    #        sys.stderr.write("\n")
    postId_commenters = getCommentsBatch(posts, doLookupToken=doLookupToken, verbose=False)
    if (verbose):
        sys.stderr.write("found %d secondary posts, %d total commenters\n" % (len(posts), sum([ len(x) for x in postId_commenters.values() ])))
    for post in posts:
        user = FbUser(post['from']['id'], post['from']['name'], doLookupToken)
        for commenter in postId_commenters.get(post['id'], []):
            if (commenter == primary):
                user_count[user] = user_count.get(user, 0) + 1
    if (verbose):
        sys.stderr.write("\tprimary commented %d posts\n" % (sum(user_count.values())))
    return user_count if (whitelist is None) else filterByKeys(user_count, whitelist)



def filterByKeys(k_v, whitelist):
    return dict([ (k, v) for k, v in k_v.items() if k in whitelist ])

def shortenToken(s):
    pos1 = s.find('access_token=')
    if (pos1 != -1):
        pos2 = s.find('&', pos1)
        return s[:pos1+10] + '...' + s[pos2-3:]
    else:
        return s


def getCounts(things, keyFunc):
    key_count = {}
    for thing in things:
        key = keyFunc(thing)
        key_count[key] = key_count.get(key, 0) + 1
    return key_count

class FbObj(object):
    def __init__(self, fbId, fbName=""):
        self.id = int(fbId)
        try:
            self.name = str(fbName)
        except UnicodeEncodeError:
            self.name = fbName.encode('ascii', 'ignore')
    def __hash__(self):
        return self.id
    def __cmp__(self, other):
        return cmp(self.id, int(other))
    def __eq__(self, other):
        return self.id == int(other)
    def __ne__(self, other):
        return self.id != int(other)
    def __int__(self):
        return self.id
    def __str__(self):
        return str(self.id) + ". " + self.name
    def __repr__(self):
        return str(self.id) + ". " + self.name

class FbUser(FbObj):
    def __init__(self, fbId, fbName="", fbAuthToken=None):
        super(FbUser, self).__init__(fbId, fbName)
        self.token = fbAuthToken
        self.friends = None # gets cached on call to friends()
        self.posts = None
        self.photos = None
        self.wall = None

    def getFriends(self):
        """Caches and returns friend set."""
        if (self.friends is None):
            sys.stderr.write("fetching friends for user %s\n" % (self))
            friendsJson = getGraphConns(self.id, 'friends', self.token, limit=10000, paging=True)
            self.friends = set([ FbUser(friend['id'], friend['name'], self.token) for friend in friendsJson ])
        return self.friends

    def getWallPosts(self):
        if (self.wall is None):
            sys.stderr.write("fetching wall for user %s\n" % (self))
            self.wall = getGraphConns(self.id, 'feed', self.token, limit=10000, paging=True)
        return self.wall

    # N.B.: returns posts and wall!
    def getAllPosts(self, fields=None):
        if (self.posts is None):
            sys.stderr.write("fetching posts for user %s\n" % (self))
            self.posts = getGraphConns(self.id, 'home', self.token, fields=fields)
        return self.posts + self.getWallPosts()

    def getUserPosts(self, fields=None):
        postsAll = self.getAllPosts(fields=fields)
        return [ p for p in postsAll if (int(p['from']['id']) == self.id) ]

    def getFriendPosts(self, fields=None):
        friends = self.getFriends()
        postsAll = self.getAllPosts(fields=fields)
        return [ p for p in postsAll if int(p['from']['id']) in friends ]

    def getUserStati(self):
        sys.stderr.write("fetching stati for user %s\n" % (self))
        return getGraphConns(self.id, 'statuses', self.token)

    # can we look in the news feed for this, or do we have to do a multi with each friend?
    def getFriendStati(self):
        sys.stderr.write("fetching friends' stati for user %s\n" % (self))
        friends = self.getFriends()
        friendId_stati = getGraphConnsBatch([ friend.id for friend in friends ], 'statuses', self.token)
        stati = friendId_stati.values()
        return list(itertools.chain(*stati))

    def getAllPhotos(self):
        if (self.photos is None):
            sys.stderr.write("fetching photos for user %s\n" % (self))
            self.photos = getGraphConns(self.id, 'photos', self.token)
        return self.photos

    def getUserPhotos(self): # photos posted by ego
        photos = self.getAllPhotos()
        return [ p for p in photos if (p['from']['id']) == self.id ]

    def getOtherPhotos(self): # photos posted by other, that have ego in them
        photos = self.getAllPhotos()
        return [ p for p in photos if (p['from']['id']) != self.id ]

    def getTaggeds(self):
        sys.stderr.write("fetching taggeds for user %s\n" % (self))
        return getGraphConns(self.id, 'tagged', self.token)

    #
    # scoring methods that return a friend_score dict
    #

    def photoCotagCounts(self, photos=None, proportional=True):
        if (photos is None):
            photos = self.getAllPhotos()
        friend_count = {}
        for p, photo in enumerate(photos):
            tags = photo['tags']['data']
            increment = 1.0/len(tags) if (proportional) else 1
            for tag in tags:
                #sys.stderr.write("photo %d, tag %s\n" % (p, str(tag)))
                if ('id' in tag):
                    friend = FbUser(int(tag['id']), tag['name'], self.token)
                    friend_count[friend] = friend_count.get(friend, 0) + increment
        return filterByKeys(friend_count, self.getFriends())

    def scoreUserPhotoCotags(self, proportional=True):
        return self.photoCotagCounts(photos=self.getUserPhotos(), proportional=proportional)

    def scoreFriendPhotoCotags(self, proportional=True):
        return self.photoCotagCounts(photos=self.getOtherPhotos(), proportional=proportional)

    def scoreFriendPhotoCountOfUser(self): # how many photos each friend has posted of ego
        return getCounts(self.getUserPhotos(), lambda p: FbUser(p['from']['id'], p['from']['name'], self.token))

    def mutualFriendCounts(self):
        url = "https://graph.facebook.com/fql?q="
        url += urllib.quote_plus("SELECT uid,name,mutual_friend_count FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=%s)" % self.id)
        url += '&format=json&access_token=' + token
        #sys.stderr.write(url + "\n")
        responses = getDataPaging(url)
        friend_count = dict([ (FbUser(int(r['uid']), r['name'], self.token), r['mutual_friend_count'] if (r['mutual_friend_count'] is not None) else 0) for r in responses ]) # user -> count
        return filterByKeys(friend_count, self.getFriends())

    # grab 'naked' urls along with links that have been posted
    def getLikedUrls(self):
        linkTups = []        
        url = "https://graph.facebook.com/fql?q="
        url += urllib.quote_plus("SELECT url FROM url_like WHERE user_id =%s" % self.id)
        url += '&format=json&access_token=' + self.token
        #sys.stderr.write(url + "\n")
        
        results = getDataPaging(url)
        #sys.stderr.write("got %d urls from url_like\n" % (len(results)))
        for link in results:
            #sys.stderr.write("\tliked url: %s\n" % (link))                            
            linkTups.append((None, link['url']))

        # this won't get you urls directly, need to do a second lookup
        url = "https://graph.facebook.com/fql?q="
        url += urllib.quote_plus("SELECT user_id, object_id, post_id, object_type FROM like WHERE user_id=%s" % self.id)
        url += '&format=json&access_token=' + self.token
        results = getDataPaging(url)
        #sys.stderr.write("got %d things from like\n" % (len(results)))

        likedIds = []
        for responseJson in results:
            #sys.stderr.write("\tliked thing (%s): %s\n" % (responseJson['object_type'], str(responseJson)))                            
            #sys.stderr.write("\thttps://graph.facebook.com/%s&access_token=%s\n" % (responseJson['object_id'], str(self.token)))                            
            likedIds.append(responseJson['object_id'])

        if (likedIds):
            likedId_info = getGraphInfoBatch(likedIds, self.token, fields="id,link")
            for likedId, info in likedId_info.items():
                #sys.stderr.write("\tliked thing info: %s\n" % str(info))
                if (info) and ('link' in info):
                    #sys.stderr.write("\tliked thing url: %s\n" % str(info['link']))
                    linkTups.append((likedId, info['link']))
        return linkTups


    def getLikedObjects(self):        
        infos = getGraphConns(self.id, 'likes', self.token)
        return [ info['id'] for info in infos ]

    def getLikedObjectUrls(self):        
        objIds = self.getLikedObjects()
        objId_info = getGraphInfoBatch(objIds, self.token, fields='id,website')
        urlTups = []
        transTab = maketrans("\t\n\r\f\v", "     ")    # we're getting some weird text back so this is a bit of a hack
        for objId, info in objId_info.items():
            if (info and info.get('website')):
                urls = info['website'].strip().translate(transTab).split()
                for url in urls:
                    #sys.stderr.write("object %s, got website: %s\n" % (objId, url))
                    if not (url.startswith('http://') or url.startswith('https://')):
                        url = 'http://' + url
                    urlTups.append((info['id'], url))
        return urlTups


    # coming up with nothing?
    def getLikedPosts(self):
        postsAll = self.getAllPosts()
                
        #postId_likers = getLikesBatch(postsAll, doLookupToken=self.token)

        postId_likersJson = getGraphConnsBatch([ post['id'] for post in postsAll ], 'likes', self.token, filtFunc=lambda x: x['id']==self.id)

        postsLikedIds = set()
        for i, (postId, likersJson) in enumerate(postId_likersJson.items()):
            if (i % 100 == 0):
                sys.stderr.write("\t%d/%d checking likers\n" % (i, len(postId_likersJson)))

            #if (self.id in [ json['id'] for json in likersJson ]):
            #    postsLiked.append(post)

            #if (self.id in [ lfor post in likersJson ])
            if (len(likersJson) > 0):
                postsLikedIds.add(postId)

        return [ post for post in postsAll if post['id'] in postsLikedIds ]

#        for post in postsAll:
#            for liker in postId_likers.get(post['id'], []):
#                if (liker.id == self.id):
#                    postsLiked.append(post)
#                    break
#        return postsLiked

    def getLikedPostLinks(self):
        postsLiked = self.getLikedPosts()
        linkTups = []    
        for post in postsLiked:
            if ('link' in post):
                linkTups.append((post['object_id'], post['link']))
        return linkTups            




    #zzz this doesn't seem to be working past month 0
    def getStreamPosts(self):
        tsNow = int(time.time())
        interval = 20*24*60*60 # twenty (20) days
        responses = []
        for intervalCount in range(10):
            ts1 = tsNow - (intervalCount + 1)*interval        
            ts2 = tsNow - intervalCount*interval
            #fql = "SELECT created_time, post_id, source_id, actor_id, target_id, type, message, likes FROM stream "
            fql = "SELECT created_time, post_id, source_id, actor_id, target_id, type FROM stream "
            #fql += "WHERE filter_key in (SELECT filter_key FROM stream_filter WHERE uid=%s AND type='newsfeed') AND is_hidden = 0 " % self.id
            fql += "WHERE filter_key in (SELECT filter_key FROM stream_filter WHERE uid=%s) " % self.id            
            fql += "AND created_time > %d AND created_time < %d" % (ts1, ts2)
            #fql += "AND created_time < %d" % (tsEnd)
            sys.stderr.write(fql + '\n')
            sys.stderr.write("interval: %s - %s\n" % (time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts1)), time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts2))))    


            url = "https://graph.facebook.com/fql?q="            
            url += urllib.quote_plus(fql)
            url += '&format=json&access_token=' + self.token
            #responsesInterval = getDataPaging(url)        
            sys.stderr.write(url + '\n')
            responsesInterval = json.load(Facebook.urlopenTimeout(url))['data']
            
            responses += responsesInterval
            sys.stderr.write("got %d posts from interval %d (%d total)\n\n" % (len(responsesInterval), intervalCount, len(responses)))
            for i, response in enumerate(responsesInterval):
                ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(response['created_time'])))    
                sys.stderr.write("\t%s %s\n" % (ts, response))
        return responses

    def scoreNonPhotoCotags(self, proportional=True):
        user_count = {}
        for t, tagged in enumerate(self.getTaggeds()):
            #sys.stderr.write("processing tagged %d: %s\n" % (t, str(tagged)))
            taggs = tagged['to']['data']
            #sys.stderr.write("tagged has %d\n\n" % (len(taggs)))
            increment = 1.0/len(taggs) if (proportional) else 1
            userFrom = FbUser(tagged['from']['id'], tagged['from']['name'], self.token)
            user_count[userFrom] = user_count.get(userFrom, 0) + increment
            for data in taggs:
                userTo = FbUser(data['id'], data['name'], self.token)
                user_count[userTo] = user_count.get(userTo, 0) + increment
        #dumpCounts(user_count)
        return filterByKeys(user_count, self.getFriends())



# quick sanity check
def auditPosts(user):
    posts = getGraphConns(user.id, 'posts', user.token, paging=True)
    feed = getGraphConns(user.id, 'feed', user.token, paging=True)
    stati = getGraphConns(user.id, 'statuses', user.token, paging=True)
    home = getGraphConns(user.id, 'home', user.token, paging=True)

    postIds = set([ p['id'] for p in posts ])
    feedIds = set([ p['id'] for p in feed ])
    statusIds = set([ p['id'] for p in stati ])
    homeIds = set([ p['id'] for p in home ])

    sys.stderr.write("\n%d posts, %d feeds intersect has %d items\n" % (len(postIds), len(feedIds), len(postIds.intersection(feedIds))))
    if (len(postIds.intersection(feedIds)) > 0):
        for post in posts:
            if (post['id'] in feedIds):
                sys.stderr.write("\t" + str(post) + "\n")
    sys.stderr.write("\n%d posts, %d stati intersect has %d items\n" % (len(postIds), len(statusIds), len(postIds.intersection(statusIds))))
    sys.stderr.write("\n%d posts, %d homes intersect has %d items\n" % (len(postIds), len(homeIds), len(postIds.intersection(homeIds))))
    sys.stderr.write("\n%d feeds, %d stati intersect has %d items\n" % (len(feedIds), len(statusIds), len(feedIds.intersection(statusIds))))
    sys.stderr.write("\n%d feeds, %d homes intersect has %d items\n" % (len(feedIds), len(homeIds), len(feedIds.intersection(homeIds))))
    sys.stderr.write("\n%d stati, %d homes intersect has %d items\n" % (len(statusIds), len(homeIds), len(statusIds.intersection(homeIds))))




def writeScores(outfileName, user, friend_scores):
    with open(outfileName, 'w') as outfile:
        for friend, friendScores in sorted(friend_scores.items(), key=lambda x: x[1], reverse=True):
            scoresCalc, scoresRaw = friendScores
            outfile.write("%s\t%s\t%s\t%s\t" % (user.id, user.name, friend.id, friend.name))
            outfile.write("\t".join([ ("%.2f" % s) for s in scoresRaw ]))
            outfile.write("\n")



guineaPigs = {}
guineaPigs['rayid'] = (500876410, 'AAABlUSrYhfIBAFkDiI9l4ZBj7hKyTywQ1WkZCkw5uiWfZAUFKh73glIsEcgS390CQas9Ya8vZAMNMUnqdZCR3EhgX3ImLRF0Xy64zspM0DQZDZD')
guineaPigs['tim'] = (1546335889, 'AAABlUSrYhfIBAMEo3RepupV7S9VjEjfFYxNZBrMQxutJ6ygidtFHafNwxz4ZA6m5Up4qQNIQkPk35EOAMeBZApZC1oZBKRtAlqREiCHYE1QZDZD')
guineaPigs['michelangelo'] = (6963, 'AAABlUSrYhfIBAA7QmZBaEotpI4KRtTqgpMXgmG4qr76qAHH4mAzNSyCwjH6kgZCvAo99fg0SZCZAnYBZCq3IAnFaq8GjV1ZCkZD')



###################################################################

if (__name__ == '__main__'):

    userId = int(sys.argv[1])
    userName = sys.argv[2]
    token = sys.argv[3]
    user = FbUser(userId, userName, token)

    friends = user.getFriends()
    token = user.token

    scores = {} # label -> user -> score

    sys.stderr.write("\n*** 1\n\n")
    scores['user-post_friend-likes'] = countPrimaryPostSecondLikes(user.getUserPosts(), whitelist=friends, doLookupToken=token, verbose=True)
    scores['user-post_friend-comms'] = countPrimaryPostSecondComms(user.getUserPosts(), whitelist=friends, doLookupToken=token, verbose=True)

    sys.stderr.write("\n*** 2\n\n")
    scores['friend-post_user-likes'] = countSecondPostPrimaryLikes(user.getFriendPosts(), user, whitelist=friends, doLookupToken=token, verbose=True)
    scores['friend-post_user-comms'] = countSecondPostPrimaryComms(user.getFriendPosts(), user, whitelist=friends, doLookupToken=token, verbose=True)

    sys.stderr.write("\n*** 3\n\n")
    scores['user-status_friend-likes'] = countPrimaryPostSecondLikes(user.getUserStati(), whitelist=friends, doLookupToken=token, verbose=True)
    scores['user-status_friend-comms'] = countPrimaryPostSecondComms(user.getUserStati(), whitelist=friends, doLookupToken=token, verbose=True)

    sys.stderr.write("\n*** 4\n\n")
    scores['friend-status_user-likes'] = countSecondPostPrimaryLikes(user.getFriendStati(), user, whitelist=friends, doLookupToken=token, verbose=True)
    scores['friend-status_user-comms'] = countSecondPostPrimaryComms(user.getFriendStati(), user, whitelist=friends, doLookupToken=token, verbose=True)

    sys.stderr.write("\n*** 5\n\n")
    scores['mutual-friend-count'] = user.mutualFriendCounts()
    scores['photo-cotags'] = user.photoCotagCounts(photos=None, proportional=True)
    scores['photo-cotags_user-posted'] = user.scoreUserPhotoCotags(proportional=True)
    scores['photo-cotags_friend-posted'] = user.scoreFriendPhotoCotags(proportional=True)
    scores['friend-photo-count'] = user.scoreFriendPhotoCountOfUser()
    scores['other-cotags'] = user.scoreNonPhotoCotags(proportional=True)

    friend_scores = {}
    for friend in user.getFriends():

        scoresCalc = []
        scoresAll = []

        s1 = scores['friend-status_user-likes'].get(friend, 0)
        s2 = scores['friend-status_user-comms'].get(friend, 0)

        s3 = scores['user-status_friend-likes'].get(friend, 0)
        s4 = scores['user-status_friend-comms'].get(friend, 0)

        s5 = scores['photo-cotags_user-posted'].get(friend, 0)
        s6 = scores['photo-cotags_friend-posted'].get(friend, 0)
        scoresCalc.append(2.0*s1 + 4.0*s2 + 0.5*s3 + 1.0*s4 + 3.0*s5 + 2.0*s6)

        s7 = scores['friend-post_user-likes'].get(friend, 0)
        s8 = scores['friend-post_user-comms'].get(friend, 0)
        scoresCalc.append(1.0*s7 + 1.5*s8)

        s9 = scores['user-post_friend-likes'].get(friend, 0)
        s10 = scores['user-post_friend-comms'].get(friend, 0)
        scoresCalc.append(s9 + s10)

        s11 = scores['other-cotags'].get(friend, 0)
        scoresCalc.append(s11)

        s12 = scores['mutual-friend-count'].get(friend, 0)
        scoresCalc.append(s12)

        scoresAll = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12]

        friend_scores[friend] = scoresCalc, scoresAll


    friendsSorted = sorted(friend_scores.items(), key=lambda x: x[1], reverse=True)
    sys.stderr.write("\n\nfriend scores:\n")
    for i, (friend, friendScores) in enumerate(friendsSorted):
        sys.stderr.write("%d. %-15s %-30s %s %s\n" % (i, friend.id, friend.name, [ "%.2f"%f for f in friendScores[0] ], [ "%.2f"%f for f in friendScores[1] ]))

    writeScores("fb_friendscores_%s.tsv" % user.id, user, friend_scores)








































##################################################################
##################################################################
#
# old stuff no longer being used, but kept around for packrat purposes


# returns alter -> alterlikecount
def getCommsLikesCounts(things, whitelist=None, verbose=False, doLookupToken=None):
    user_likes = {}
    user_comms = {}

    if (verbose):
        sys.stderr.write("finding likes, comments for %d things\n" % (len(things)))
        sys.stderr.write("lookup token: %s\n" % (str(doLookupToken)))

        sys.stderr.write("%s\n\n" % (str(things)))

    for t, thing in enumerate(things):
        if (verbose):
            sys.stderr.write("thing %d/%d: %s\n" % (t, len(things), str(thing)))
#        if ('likes' in thing):
#            for likerJson in thing['likes']['data']:
#                if (verbose):
#                    sys.stderr.write("\tlike: %s\n" % (str(likerJson)))
#                liker = FbUser(likerJson['id'], likerJson['name'])
#                user_likes[liker] = user_likes.get(liker, 0) + 1
#        else:
#            if (verbose):
#                sys.stderr.write("\tno likes\n")

#        if ('comments' in thing):
#            for commentJson in thing['comments']['data']:
#                if (verbose):
#                    sys.stderr.write("\tcomment: %s\n" % (str(commentJson)))
#                commenter = FbUser(commentJson['from']['id'], commentJson['from']['name'])
#                user_comms[commenter] = user_comms.get(commenter, 0) + 1
#        else:
#            if (verbose):
#                sys.stderr.write("\tno likes\n")
        for user in getLikes(thing, doLookupToken=doLookupToken):
            user_likes[user] = user_likes.get(user, 0) + 1
        for user in getComments(thing, doLookupToken=doLookupToken):
            user_comms[user] = user_comms.get(user, 0) + 1

        if (verbose):
            sys.stderr.write("\n")

    user_counts = {}
    for user in set(user_likes.keys() + user_comms.keys()):
        if (whitelist is None) or (user in whitelist):
            user_counts[user] = (user_likes.get(user, 0), user_comms.get(user, 0))
    return user_counts





# returns alter -> egolikecount, the number of likes ego has placed on items from each alter
def getCommsLikesCountsFromEgo(ego, things, keyFunc=lambda x: x['from'], whitelist=None, verbose=False, doLookupToken=None):
    user_likes = {}
    user_comms = {}
    for t, thing in enumerate(things):
        if (verbose):
            sys.stderr.write("thing %d/%d: %s\n" % (t, len(things), str(thing)))

        user = keyFunc(thing)

#        if ('likes' in thing) and ('data' in thing['likes']):
#            for likerJson in thing['likes']['data']:
#                if (likerJson['id'] == ego):
#                    user_likes[user] = user_likes.get(user, 0) + 1
#        if ('comments' in thing) and ('data' in thing['comments']):
#            for commentJson in thing['comments']['data']:
#                if (commentJson['from']['id'] == ego):
#                    user_comms[user] = user_comms.get(user, 0) + 1
        for user in getLikes(thing, doLookupToken=doLookupToken):
            user_likes[user] = user_likes.get(user, 0) + 1
        for user in getComments(thing, doLookupToken=doLookupToken):
            user_comms[user] = user_comms.get(user, 0) + 1

    user_counts = {}
    for user in set(user_likes.keys() + user_comms.keys()):
        if (whitelist is None) or (user in whitelist):
            user_counts[user] = (user_likes.get(user, 0), user_comms.get(user, 0))
    return user_counts



def getPhotos(userId, token, lim=10000):
    return getGraphConns(userId, 'photos', token, limit=lim)


def getFeedPosts(userId, token, fields=None, fromIds=None, lim=10000):
    posts = getGraphConns(userId, 'home', token, fields=fields, limit=lim, paging=True)
    if (fromIds is not None):
        sys.stderr.write("got %d unfiltered posts, filtering for %d ids\n" % (len(posts), len(fromIds)))
        posts = [ p for p in posts if int(p['from']['id']) in set(fromIds) ]
    sys.stderr.write("got %d posts\n\n" % len(posts))
    return posts


def getFeedPosts(userId, token, fields=None, fromIds=None, lim=10000):
    posts = getGraphConns(userId, 'home', token, fields=fields, limit=lim, paging=True)
    if (fromIds is not None):
        sys.stderr.write("got %d unfiltered posts, filtering for %d ids\n" % (len(posts), len(fromIds)))
        posts = [ p for p in posts if int(p['from']['id']) in set(fromIds) ]
    sys.stderr.write("got %d posts\n\n" % len(posts))
    return posts

def getStati(userId, token, lim=10000):
    return getGraphConns(userId, 'statuses', token, limit=lim, paging=False)

def getTaggeds(userId, token, lim=10000):
    return getGraphConns(userId, 'tagged', token, limit=lim)

def getPhotos(userId, token, lim=10000):
    return getGraphConns(userId, 'photos', token, limit=lim)

def getPostComments(postId, token, fields=None, lim=10000):
    return getGraphConns(postId, 'comments', token, fields, limit=lim)

def getPostLikes(postId, token, fields=None, lim=10000):
    return getGraphConns(postId, 'likes', token, fields, limit=lim)

def getPostCommentsBatch(postIds, token, fields=None, limit=100000):
    return getGraphConnsBatch(postIds, "comments", token, fields, limit=limit)

# returns (userId, userName) -> number of tags
def getTaggedOtherCounts(userId, token, friendsOnly=True, limit=10000):
    # id, from, to, picture, link, name, caption, description, properties, icon, actions, type, application, created_time, and updated_time
    userKey_taggedCount = {}
    for tagged in getTaggeds(userId, token, lim=limit):
        sys.stderr.write(str(tagged) + "\n\n")
        fromId = tagged['from']['id']
        fromName = tagged['from']['name']
        fromKey = FbObj(fromId, fromName)
        for data in tagged['to']['data']:
            toId = data['id']
            toName = data['name']
            toKey = FbObj(toId, toName)
            sys.stderr.write("%10s %20s <---> %-10s %-20s\n" % (fromId, fromName, toId, toName))
            userKey_taggedCount[fromKey] = userKey_taggedCount.get(fromKey, 0) + 1
            userKey_taggedCount[toKey] = userKey_taggedCount.get(toKey, 0) + 1

    if (friendsOnly):
        userKey_taggedCount = filterByKeys(userKey_taggedCount, getFriends(userId, token))
    dumpCounts(userKey_taggedCount)
    return userKey_taggedCount


# returns (userId, userName) -> number of comments on stati
def getStatiCommenterCounts(userId, token, normalize=False, friendsOnly=True, limit=10000):
    fromKey_commentCount = {}
    stati = getStati(userId, token, limit)
    for status in stati:
        if ('comments' in status):
            for comment in status['comments']['data']:
                fromKey = FbObj(comment['from']['id'], comment['from']['name'])
                fromKey_commentCount[fromKey] =  fromKey_commentCount.get(fromKey, 0) + 1
    if (normalize):
        fromKey_commentCount = dict([ [k, v/float(len(stati))] for k, v in fromKey_commentCount.items() ])
    if (friendsOnly):
        fromKey_commentCount = filterByKeys(fromKey_commentCount, getFriends(userId, token))
    dumpCounts(fromKey_commentCount)
    return fromKey_commentCount

# returns (userId, userName) -> number of comments on stati
def getStatiLikeCounts(userId, token, normalize=False, friendsOnly=True, limit=10000):
    fromKey_count = {}
    stati = getStati(userId, token, limit)
    for status in stati:
        if ('likes' in status):
            #sys.stderr.write("status:\n")
            #for k, v in status.items():
            #    sys.stderr.write("\t%s: %s\n" % (k, v))
            #sys.stderr.write("\n")
            for like in status['likes']['data']:
                fromKey = FbObj(like['id'], like['name'])
                fromKey_count[fromKey] =  fromKey_count.get(fromKey, 0) + 1
    if (normalize):
        fromKey_count = dict([ [k, v/float(len(stati))] for k, v in fromKey_count.items() ])
    if (friendsOnly):
        fromKey_count = filterByKeys(fromKey_count, getFriends(userId, token))
    dumpCounts(fromKey_count)
    return fromKey_count




# returns (userId, userName) -> number of comments on feed posts placed by other friends Facebook.getFeedCommenterCounts(500876410, AAABlUSrYhfIBAFkDiI9l4ZBj7hKyTywQ1WkZCkw5uiWfZAUFKh73glIsEcgS390CQas9Ya8vZAMNMUnqdZCR3EhgX3ImLRF0Xy64zspM0DQZDZD, limit=10000)
def getFeedCommenterCounts(userId, token, friendsOnly=True, limit=10000):

    friends = getFriends(userId, token)
    friendIds = set([ f.id for f in friends ])
    friendIds.add(userId) # you are your own friend here

    posts = getFeedPosts(userId, token, 'id,comments,type,from', friendIds, limit)
    sys.stderr.write("posts (%d): %s\n\n" % (len(posts), str(posts)[:20]))

    ## make one call per post
    #fromIdName_commentCount = {}
    #for i, post in enumerate(posts):
    #    if (post['comments']['count'] > 0):
    #        sys.stderr.write("%d/%d grabbing %d comments for post %s\n" % (i, len(posts), post['comments']['count'], post['id']))
    #        try:
    #            comments = getPostComments(post['id'], token, "from", 10000)
    #        except:
    #            sys.stderr.write("error fetching comments for post %s\n" % (post['id']))
    #            continue
    #        #sys.stderr.write("post %s comments:\n%s\n\n" % (post['id'], comments))
    #        for comment in comments:
    #            fromId = comment['from']['id']
    #            fromName = comment['from']['name']
    #            fromKey = (fromId, fromName)
    #            fromIdName_commentCount[fromKey] = fromIdName_commentCount.get(fromKey, 0) + 1
    #    else:
    #        sys.stderr.write("%d/%d no comments for post %s, skipping\n" % (i, len(posts), post['id']))

    # batch it
    postsIdsWithComments = [ p for p in posts if (p['comments']['count'] > 0) ]
    sys.stderr.write("found %d/%d posts with comments\n" % (len(postsIdsWithComments), len(posts)))

    fromIdName_commentCount = {}
    chunkSize = 35
    i = 0
    while (i < len(postsIdsWithComments)):
        postsChunk = postsIdsWithComments[i:i+chunkSize]
        postIdsChunk = [ p['id'] for p in postsChunk ]

        sys.stderr.write("grabbing comments for posts %d-%d\n" % (i, i+chunkSize))
        try:
            postId_comments = getPostCommentsBatch(postIdsChunk, token, fields="from")
        except Exception, e:
            sys.stderr.write("ERROR fetching comments for posts %d-%d\n" % (i, i+chunkSize))
            sys.stderr.write(str(e) + "\n")
            i += chunkSize
            continue
        for postId, comments in postId_comments.items():
            if (comments is None):
                sys.stderr.write("ERROR null comments for post %s\n" % (postId))
                continue
            sys.stderr.write("%d comments for post %s: %s\n" % (len(comments['data']), postId, str(comments['data'])[:100]))
            for comment in comments['data']:
                fromId = comment['from']['id']
                fromName = comment['from']['name']
                fromKey = FbObj(fromId, fromName)
                fromIdName_commentCount[fromKey] = fromIdName_commentCount.get(fromKey, 0) + 1
        i += chunkSize

    nonfriends = 0
    for user, commentCount in sorted(fromIdName_commentCount.items(), key=lambda x: x[1], reverse=True):
        if (user.id in friendIds):
            sys.stderr.write("comments from %-16s. %-20s: %d\n" % (user.id, user.name, commentCount))
        else:
            nonfriends += 1
    sys.stderr.write("found %d people we don't know'\n" % nonfriends)

    if (friendsOnly):
        fromIdName_commentCount = filterByKeys(fromIdName_commentCount, getFriends(userId, token))
    return fromIdName_commentCount


def getFriendsFeedLiked(userId, token, friendsOnly=True, limit=10000):

    friends = getFriends(userId, token)
    friendIds = set([ f.id for f in friends ])
    friendIds.add(userId) # you are your own friend here

    posts = getFeedPosts(userId, token, 'id,comments,type,from', friendIds, limit)
    #sys.stderr.write("posts (%d): %s\n\n" % (len(posts), str(posts)[:20]))


    friend_count = {}
    for p, post in enumerate(posts):
        sys.stderr.write("post %d: %s\t%s\n%s\n" % (p, post.get('updated_time',""), post['from']['name'], post))
        for k, v in post.items():
            sys.stderr.write("\t%s: %s\n" % (k, v))
        sys.stderr.write("\n")



        # likes: {u'count': 1, u'data': [{u'name': u'Shannon Cooper', u'id': u'1190900083'}]}
        if ('likes' in post):
            for liker in post['likes']['data']:
                likerId = liker['id']
                if (int(likerId) == int(userId)):

                    friendKey = FbObj(int(post['from']['id']), post['from']['name'])
                    friend_count[friendKey] = friend_count.get(friendKey, 0) + 1

    if (friendsOnly):
        friend_count = filterByKeys(friend_count, getFriends(userId, token))
    dumpCounts(friend_count)
    return friend_count





# returns (friendId, friendName) -> # feed posts
def getFriendsFeedCounts(userId, token, friendsOnly=True, limit=10000):
    posts = getFeedPosts(userId, token, lim=limit)
    sys.stderr.write("got %d posts\n" % len(posts))
    friend_count = {}
    for p, post in enumerate(posts):
        sys.stderr.write("post %d: %s\t%s\n%s\n\n" % (p, post['updated_time'], post['from']['name'], post))
        friendKey = FbObj(int(post['from']['id']), post['from']['name'])
        friend_count[friendKey] = friend_count.get(friendKey, 0) + 1

    if (friendsOnly):
        friend_count = filterByKeys(friend_count, getFriends(userId, token))
    dumpCounts(friend_count)
    return friend_count

# returns (friendId, friendName) -> # mutual friends
def getFriendsMutualCounts(userId, token, friendsOnly=True, limit=10000):
    url = "https://graph.facebook.com/fql?q="
    url += urllib.quote_plus("SELECT uid,name,mutual_friend_count FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1=%s)" % userId)
    url += '&format=json&access_token=' + token
    sys.stderr.write(url + "\n")
    responses = getDataPaging(url, limit=limit)
    user_muts = dict([ (FbObj(int(r['uid']), r['name']), r['mutual_friend_count'] if (r['mutual_friend_count'] is not None) else 0) for r in responses ]) # (id, name) -> count
    if (friendsOnly):
        user_muts = filterByKeys(user_muts, getFriends(userId, token))
    dumpCounts(user_muts)
    return user_muts

# returns (friendId, friendName) -> # photos co-tagged posts
def getPhotoCotagCounts(userId, token, proportional=True, friendsOnly=True, limit=10000):
    photos = getPhotos(userId, token, lim=limit)
    friend_count = {}
    for p, photo in enumerate(photos):
        tags = photo['tags']['data']
        increment = 1.0/len(tags) if (proportional) else 1
        for tag in tags:
            sys.stderr.write("photo %d, tag %s\n" % (p, str(tag)))
            if ('id' in tag):
                friendKey = FbObj(int(tag['id']), tag['name'])
                friend_count[friendKey] = friend_count.get(friendKey, 0) + increment

    if (friendsOnly):
        friend_count = filterByKeys(friend_count, getFriends(userId, token))
    dumpCounts(friend_count)
    return friend_count

# returns (friendId, friendName) -> # photos of ego posted by friend + friend posted by ego
def getPhotoPostCounts(userId, token, proportional=True, friendsOnly=True, limit=10000):
    photos = getPhotos(userId, token, lim=limit)
    other_count = {}
    for p, photo in enumerate(photos):
        fromId = int(photo['from']['id'])
        fromName = photo['from']['name']
        increment = 1.0/len(photo['tags']['data']) if (proportional) else 1
        if (fromId == userId): # photo was posted by userId
            for tag in photo['tags']['data']:
                #sys.stderr.write("photo %d, tag %s\n" % (p, str(tag)))
                if ('id' in tag):
                    friend = FbObj(int(tag['id']), tag['name'])
                    other_count[friend] = other_count.get(friend, 0) + increment
        else: # photo was taken by someone else
            other = FbObj(fromId, fromName)
            other_count[other] = other_count.get(other, 0) + increment
    if (friendsOnly):
        other_count = filterByKeys(other_count, getFriends(userId, token))
    dumpCounts(other_count)
    return other_count


# this one doesn't work right, since some may not make their total photos available via privacy settings
def getPhotoCotagCountsNorm(userId, token, minThresh=3, chunkSize=35, friendsOnly=True, limit=10000):
#    friend_count = getPhotoCotagCounts(userId, token, friendsOnly=True, limit=10000)
#    sys.stderr.write("friend_count: %s\n" % str(friend_count))

#    friend_countNorm = {}
#    friends = [ f for f in friend_count.keys() if (friend_count[f] >= minThresh) ]
#    for i in range(0, len(friends) + chunkSize, chunkSize):
#        start = i
#        end = i + chunkSize
#        friendsChunk = friends[start:end]
#        sys.stderr.write("friendsChunk %s\n" % str(friendsChunk))
#        friend_photos = getGraphConnsBatch(friendsChunk, 'photos', token, fields='id')
#        sys.stderr.write("friend_photos %s\n" % str(friend_photos))
#        for friend, photos in friend_photos.items():
#            sys.stderr.write("\tfriend %s photos: %s\n" % (str(friend), str(photos)))
#            norm = len(photos) if (photos is not None) else friend_count[friend]
#            friend_countNorm[friend] = float(friend_count[friend])/norm
    return friend_countNorm



def rankCounts(k_c):
    return sorted(k_c.items(), key=lambda x: x[1], reverse=True)

def dumpCounts(k_c, limit=sys.maxint):
    if (k_c):
        longest = max([ len(str(k)) for k in k_c.keys() ])
        for k, count in rankCounts(k_c)[:limit]:
            sys.stderr.write(str(k).rjust(longest + 1) + " " + str(count) + "\n")

def dumpUserList(k_c, limit=sys.maxint, stream=sys.stderr, scores=False):
    ret = ""
    for i, (k, count) in enumerate(rankCounts(k_c)[:limit]):
        s = "%d. %-30s" % (i, str(k))
        if (scores):
            s += "\t" + str(count)
        s += "\n"
        ret += s
        stream.write(s)
    return ret





def getAllRankings(userId, token):
    label_rankingFunc = {}
    #label_rankingFunc["muts"] = getFriendsMutualCounts
    #label_rankingFunc["feeds"] = getFriendsFeedCounts
    #label_rankingFunc["feedcomms"] = getFeedCommenterCounts
    #label_rankingFunc["statcomms norm"] = lambda u,t,f,l: getStatiCommenterCounts(u, t, normalize=True, friendsOnly=f, limit=l)
    #label_rankingFunc["statcomms"] = lambda u,t,f,l: getStatiCommenterCounts(u, t, normalize=False, friendsOnly=f, limit=l)
    #label_rankingFunc["tagged"] = getTaggedOtherCounts
    #label_rankingFunc["cophoto prop"] = lambda u,t,f,l: getPhotoCotagCounts(u, t, proportional=True, friendsOnly=f, limit=l)
    #label_rankingFunc["cophoto"] = lambda u,t,f,l: getPhotoCotagCounts(u, t, proportional=False, friendsOnly=f, limit=l)
    #label_rankingFunc["photopost prop"] = lambda u,t,f,l: getPhotoPostCounts(u, t, proportional=True, friendsOnly=f, limit=l)
    #label_rankingFunc["photopost"] = lambda u,t,f,l: getPhotoPostCounts(u, t, proportional=False, friendsOnly=f, limit=l)
    label_rankingFunc["statlikes"] = lambda u,t,f,l: getStatiLikeCounts(u, t, normalize=False, friendsOnly=f, limit=l)


    label_rankingFunc["feedlikes"] = getFriendsFeedLiked



    friends = set()
    label_ranking = {}
    outs = ""
    for label, rankingFunc in sorted(label_rankingFunc.items()):
        friend_score = rankingFunc(userId, token, True, 10000)
        friends.update(friend_score.keys())
        label_ranking[label] = friend_score
        outs += "List %s:\n" % label
        outs += dumpUserList(friend_score, 20, scores=True) + "\n"*4
    sys.stderr.write("\n"*4)
    sys.stdout.write(outs)



    # blended
    friend_score = {}
    for friend in friends:
        scoreList = []
        scoreList.append(label_ranking["statcomms"].get(friend, 0) + label_ranking["cophoto prop"].get(friend, 0))
        scoreList.append(label_ranking["tagged"].get(friend, 0))
        scoreList.append(label_ranking["feeds"].get(friend, 0))
        scoreList.append(label_ranking["muts"].get(friend, 0))
        friend_score[friend] = scoreList

    dumpUserList(friend_score, 20, scores=True)


#def harmonic(x, y):
#    return float(2*x*y)/(x+y) if ((x + y) > 0) else 0

#def getGraphApiConns(thingId, connType, token, fields=None, limit=1000, timeout=None):
#    url = "https://graph.facebook.com/%s/%s?access_token=%s" % (thingId, connType, token)
#    if (fields is not None):
#        url += "&fields=%s" % fields
#    datas = getGraphConns(url, limit, timeout)
#    sys.stderr.write("got %d %s\n" % (len(datas), connType))
#    return datas
