#!/usr/bin/python
import sys
import urllib
import urllib2
import json
import time
import datetime
import subprocess
from joblib import Parallel, delayed
from collections import defaultdict
import logging
logging.basicConfig(format='%(asctime)s\t%(levelname)s\t%(message)s',
					filename='demo.log',
					level=logging.DEBUG)
import ReadStreamDb



NUM_JOBS = 5
STREAM_NUM_DAYS = 120
STREAM_CHUNK_DAYS = 10

class STREAMTYPE:
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

FQL_STREAM_CHUNK = " ".join("""SELECT created_time, post_id, source_id, target_id, type FROM stream
								WHERE source_id=%s AND %d <= created_time AND created_time < %d LIMIT 5000""".split())
FQL_POST_COMMS = "SELECT fromid FROM comment WHERE post_id IN (SELECT post_id FROM %s WHERE type != " + str(STREAMTYPE.STATUS_UPDATE) + ")"
FQL_POST_LIKES = "SELECT user_id FROM like WHERE post_id IN (SELECT post_id FROM %s WHERE type != " + str(STREAMTYPE.STATUS_UPDATE) + ")"
FQL_STAT_COMMS = "SELECT fromid FROM comment WHERE post_id IN (SELECT post_id FROM %s WHERE type = " + str(STREAMTYPE.STATUS_UPDATE) + ")"
FQL_STAT_LIKES = "SELECT user_id FROM like WHERE post_id IN (SELECT post_id FROM %s WHERE type = " + str(STREAMTYPE.STATUS_UPDATE) + ")"





class StreamCounts(object):
	def __init__(self, userId, stream=[], postLikers=[], postCommers=[], statLikers=[], statCommers=[]):
		self.id = userId
		self.stream = []
		self.friendId_postLikeCount = defaultdict(int)
		self.friendId_postCommCount = defaultdict(int)
		self.friendId_statLikeCount = defaultdict(int)
		self.friendId_statCommCount = defaultdict(int)
		#sys.stderr.write("got post likers: %s\n" % (str(postLikers)))
		#sys.stderr.write("got post commers: %s\n" % (str(postCommers)))
		#sys.stderr.write("got stat likers: %s\n" % (str(statLikers)))
		#sys.stderr.write("got stat commers: %s\n" % (str(statCommers)))
		self.stream.extend(stream)
		self.addPostLikers(postLikers)
		self.addPostCommers(postCommers)
		self.addStatLikers(statLikers)
		self.addStatCommers(statCommers)
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
		return self		
	def __add__(self, other):
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
		#ret += "\n"
		#ret += "stream %s\n" % (id(self.stream))
		#for i in range(min(5, len(self.stream))):
			#ret += "\t" + str(self.stream[i]) + "\n"
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

	def getPostLikes(self, friendId):
		return self.friendId_postLikeCount.get(friendId, 0)
	def getPostComms(self, friendId):
		return self.friendId_postCommCount.get(friendId, 0)
	def getStatLikes(self, friendId):
		return self.friendId_statLikeCount.get(friendId, 0)
	def getStatComms(self, friendId):
		return self.friendId_statCommCount.get(friendId, 0)
	def getStatComms(self, friendId):
		return self.friendId_statCommCount.get(friendId, 0)

	def getFriendIds(self):
		fIds = set()
		fIds.update(self.friendId_postLikeCount.keys())
		fIds.update(self.friendId_postCommCount.keys())
		fIds.update(self.friendId_statLikeCount.keys())
		fIds.update(self.friendId_statCommCount.keys())
		return fIds		
	def getFriendRanking(self):
		fIds = self.getFriendIds()
		friendId_total = defaultdict(int)
		for fId in fIds:
			friendId_total[fId] += self.friendId_postLikeCount.get(fId, 0)*2
			friendId_total[fId] += self.friendId_postCommCount.get(fId, 0)*4
			friendId_total[fId] += self.friendId_statLikeCount.get(fId, 0)*2
			friendId_total[fId] += self.friendId_statCommCount.get(fId, 0)*4
		return sorted(fIds, key=lambda x: friendId_total[x], reverse=True)


class Edge(object):
	def __init__(self, primInfo, secInfo,
					inPostLikes, inPostComms, inStatLikes, inStatComms, 
					outPostLikes, outPostComms, outStatLikes, outStatComms, 
					mutuals):
		self.primary = primInfo
		self.secondary = secInfo
		self.inPostLikes = inPostLikes
		self.inPostComms = inPostComms
		self.inStatLikes = inStatLikes
		self.inStatComms = inStatComms
		self.outPostLikes = outPostLikes
		self.outPostComms = outPostComms
		self.outStatLikes = outStatLikes
		self.outStatComms = outStatComms
		self.mutuals = mutuals
	def __str__(self):
		ret = ""
		for c in[self.inPostLikes, self.inPostComms, self.inStatLikes, self.inStatComms, self.outPostLikes, self.outPostComms, self.outStatLikes, self.outStatComms, self.mutuals]:
			ret += "%2s " % str(c)
		return ret
		
	def prox(self, inPostLikesMax, inPostCommsMax, inStatLikesMax, inStatCommsMax,
			outPostLikesMax, outPostCommsMax, outStatLikesMax, outStatCommsMax, mutsMax):
		
		countMaxWeightTups = [
			# px3
			(self.mutuals, mutsMax, 1.0),

			# px4
			(self.inPostLikes, inPostLikesMax, 1.0),
			(self.inPostComms, inPostCommsMax, 1.0),
			(self.inStatLikes, inStatLikesMax, 2.0),
			(self.inStatComms, inStatCommsMax, 1.0),
			#zzz need other tags					

			# px5
			(self.outPostLikes, outPostLikesMax, 2.0),
			(self.outPostComms, outPostCommsMax, 3.0),
			(self.outStatLikes, outStatLikesMax, 2.0),
			(self.outStatComms, outStatCommsMax, 16.0)
			#zzz need other tags								
		]
		pxTotal = 0.0
		weightTotal = 0.0
		for count, countMax, weight in countMaxWeightTups:
			if (countMax):
				pxTotal += float(count)/countMax*weight
				weightTotal += weight
		return pxTotal / weightTotal				

	def toDb(self, conn=None):
		if (conn is None):
			conn = ReadStreamDb.getConn()
		curs = conn.cursor()
		sql = """
			INSERT OR REPLACE INTO edges VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		"""
		params = (self.primary.id, self.secondary.id, 
				self.inPostLikes, self.inPostComms, self.inStatLikes, self.inStatComms,
				self.outPostLikes, self.outPostComms, self.outStatLikes, self.outStatComms,
				self.mutuals, time.time())
		curs.execute(sql, params)
		conn.commit()


class EdgeSC1(Edge):
	def __init__(self, userInfo, friendInfo, userStreamCount):
		self.primary = userInfo
		self.secondary = friendInfo
		self.inPostLikes = userStreamCount.getPostLikes(friendInfo.id)
		self.inPostComms = userStreamCount.getPostComms(friendInfo.id)
		self.inStatLikes = userStreamCount.getStatLikes(friendInfo.id)
		self.inStatComms = userStreamCount.getStatComms(friendInfo.id)
		self.outPostLikes = None
		self.outPostComms = None
		self.outStatLikes = None
		self.outStatComms = None
		self.mutuals = friendInfo.mutuals

class EdgeSC2(Edge):
	def __init__(self, userInfo, friendInfo, userStreamCount, friendStreamCount):
		self.primary = userInfo
		self.secondary = friendInfo
		self.inPostLikes = userStreamCount.getPostLikes(friendInfo.id)
		self.inPostComms = userStreamCount.getPostComms(friendInfo.id)
		self.inStatLikes = userStreamCount.getStatLikes(friendInfo.id)
		self.inStatComms = userStreamCount.getStatComms(friendInfo.id)
		self.outPostLikes = friendStreamCount.getPostLikes(userInfo.id)
		self.outPostComms = friendStreamCount.getPostComms(userInfo.id)
		self.outStatLikes = friendStreamCount.getStatLikes(userInfo.id)
		self.outStatComms = friendStreamCount.getStatComms(userInfo.id)
		self.mutuals = friendInfo.mutuals


class UserInfo(object):
	def __init__(self, uid, first_name, last_name, sex, birthday):
		self.id = uid
		self.fname = first_name
		self.lname = last_name
		self.gender = sex

		self.birthday = birthday
		self.age = int((datetime.date.today() - self.birthday).days/365.25) if (birthday) else None

class FriendInfo(UserInfo):
	def __init__(self, uid, first_name, last_name, sex, birthday, mutual_friend_count):
		UserInfo.__init__(self, uid, first_name, last_name, sex, birthday)
		self.mutuals = mutual_friend_count


def getFriendsFb(userId, token):
	fql = """SELECT uid, first_name, last_name, sex, birthday_date, mutual_friend_count FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = %s)""" % (userId)
	url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=' + token	
	responseFile = urllib2.urlopen(url, timeout=60)
	responseJson = json.load(responseFile)
	#sys.stderr.write("responseJson: " + str(responseJson) + "\n\n")
	#friendIds = [ rec['uid2'] for rec in responseJson['data'] ]
	#friendTups = [ (rec['uid'], rec['name'], rec['mutual_friend_count']) for rec in responseJson['data'] ]
	#return friendTups
	friends = []
	for rec in responseJson['data']:
		f = FriendInfo(rec['uid'], rec['first_name'], rec['last_name'], rec['sex'], dateFromFb(rec['birthday_date']), rec['mutual_friend_count'])
		friends.append(f)
	return friends


def getUserFb(userId, token):
	fql = """SELECT uid, first_name, last_name, sex, birthday_date FROM user WHERE uid=%s""" % (userId)
	url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=' + token	
	responseFile = urllib2.urlopen(url, timeout=60)
	responseJson = json.load(responseFile)
	rec = responseJson['data'][0]
	user = UserInfo(rec['uid'], rec['first_name'], rec['last_name'], rec['sex'], dateFromFb(rec['birthday_date']))
	return user


def dateFromFb(dateStr):
	if (dateStr):
		dateElts = dateStr.split('/')
		if (len(dateElts) == 3): 
			m, d, y = dateElts
			return datetime.date(int(y), int(m), int(d))
	return None

def dateFromIso(dateStr):
	if (dateStr):
		dateElts = dateStr.split('-')
		if (len(dateElts) == 3): 
			y, m, d = dateElts
			return datetime.date(int(y), int(m), int(d))
	return None		





# def getNameFb(userId, token):
# 	fql = """SELECT uid, name FROM user WHERE uid=%s""" % (userId)
# 	url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=' + token	
# 	responseFile = urllib2.urlopen(url, timeout=60)
# 	responseJson = json.load(responseFile)
# 	return responseJson['data'][0]['name']







	# def __init__(self, conn, primId, secId):
	# 	if (conn is None):
	# 		conn = ReadStreamDb.getConn()
	# 	curs = conn.cursor()
	# 	sql = """
	# 			SELECT prim_id, sec_id INTEGER,
	# 					in_post_likes, in_post_comms, in_stat_likes, in_stat_comms,
	# 					out_post_likes, out_post_comms, out_stat_likes, out_stat_comms, 
	# 					mut_friends, updated
	# 			FROM edges
	# 			WHERE prim_id=%s AND sec_id=%d
	# 	""" % (primId, secId)
	# 	curs.execute(sql)
	# 	elts = curs.fetchone()
	# 	self.id1, self.id2 = elts[0:2]
	# 	self.inPostLikes, self.inPostComms, self.inStatLikes, self.inStatComms = elts[2:6]
	# 	self.outPostLikes, self.outPostComms, self.outStatLikes, self.outStatComms = elts[6:10]
	# 	self.mutuals = elts[10]

# def getNamesDb(conn, userIds):
# 	sql = """
# 		SELECT prim_id, name FROM users WHERE prim_id IN (%s)
# 	""" % (", ".join(map(str, userIds)))
# 	curs = conn.cursor()
# 	curs.execute(sql)
# 	userId_userName = {}
# 	for userId, userName in curs:
# 		userId_userName[userId] = userName
# 	return userId_userName

def getUserDb(conn, userId):
	sql = """SELECT fbid, fname, lname, gender, birthday, token, friend_token, updated FROM users WHERE fbid=%s""" % userId
	logging.debug(sql)
	curs = conn.cursor()
	curs.execute(sql)

	rec = curs.fetchone()
	logging.debug(str(rec))

	fbid, fname, lname, gender, birthday, token, friend_token, updated = rec

	return UserInfo(fbid, fname, lname, gender, dateFromIso(birthday))


def getFriendEdgesDb(conn, primId, includeOutgoing=False):
	if (conn is None):
		conn = ReadStreamDb.getConn()
	curs = conn.cursor()
	sql = """
			SELECT prim_id, sec_id,
					in_post_likes, in_post_comms, in_stat_likes, in_stat_comms,
					out_post_likes, out_post_comms, out_stat_likes, out_stat_comms, 
					mut_friends, updated
			FROM edges
			WHERE prim_id=?
	""" 
	if (includeOutgoing):
		sql += """
			AND out_post_likes IS NOT NULL 
			AND out_post_comms IS NOT NULL 
			AND out_stat_likes IS NOT NULL
			AND out_stat_comms IS NOT NULL
		"""
	curs.execute(sql, (primId,))
	eds = []
	primary = getUserDb(conn, primId)
	for pId, sId, inPstLk, inPstCm, inStLk, inStCm, outPstLk, outPstCm, outStLk, outStCm, muts, updated in curs:
		secondary = getUserDb(conn, sId)
		eds.append(Edge(primary, secondary, inPstLk, inPstCm, inStLk, inStCm, outPstLk, outPstCm, outStLk, outStCm, muts))
	return eds

def updateUserDb(conn, user, tok, tokFriend):
	# can leave tok or tokFriend blank, in that case it will not overwrite

	sql = "INSERT OR REPLACE INTO users (fbid, fname, lname, gender, birthday, token, friend_token, updated) "
	if (tok is None):
		sql += "VALUES (?, ?, ?, ?, ?, (SELECT token FROM users WHERE fbid=?), ?, ?)"
		params = (user.id, user.fname, user.lname, user.gender, str(user.birthday), user.id, tokFriend, time.time())
	elif (tokFriend is None):
		sql += "VALUES (?, ?, ?, ?, ?, ?, (SELECT friend_token FROM users WHERE fbid=?), ?)"
		params = (user.id, user.fname, user.lname, user.gender, str(user.birthday), tok, user.id, time.time())
	else:
		sql += "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
		params = (user.id, user.fname, user.lname, user.gender, str(user.birthday), tok, tokFriend, time.time())
	curs = conn.cursor()
	curs.execute(sql, params)
	conn.commit()	

def updateFriendEdgesDb(conn, userId, tok, readFriendStream=True, overwrite=True):

	# get an up-to-date friend list
	#friendId_friend = {}
	#for friendId, friendName, friendMuts in getFriendsFb(userId, tok):
	#	friendId_info[friendId] = (friendName, friendMuts)
	#for friend in getFriendsFb(userId, tok):
	#	friendId_friend[friend.id] = friend	
	#logging.debug("got %d friends total", len(friendId_info))

	friends = getFriendsFb(userId, tok)
	logging.debug("got %d friends total", len(friends))

	# if we're not overwriting, see what we have saved
	if (overwrite):
		#friendQueue = friendId_friend.keys()
		friendQueue = friends
	else:
		edgesDb = getFriendEdgesDb(conn, userId, includeOutgoing=readFriendStream)
		friendIdsPrev = set([ e.secondary.id for e in edgesDb ])
		friendQueue = [ f for f in friends if f.id not in friendIdsPrev ]

		#friendId_edge = dict([ (e.id2, e) for e in edgesDb ])
		#friendQueue = []
		#for fId in friendId_friend.keys():
		#	if fId not in friendId_edge: # we haven't pulled this edge already (or we did, but not outgoing) 
		#		friendQueue.append(fId)

	logging.info('reading stream for user %s, %s', userId, tok)
	sc = readStreamParallel(userId, tok, STREAM_NUM_DAYS, STREAM_CHUNK_DAYS, NUM_JOBS)
	logging.debug('got %s', str(sc))

	# sort all the friends by their stream rank (if any) and mutual friend count
	friendId_streamrank = dict(enumerate(sc.getFriendRanking()))
	logging.debug("got %d friends ranked", len(friendId_streamrank))
	#friendQueue.sort(key=lambda x: (friendId_streamrank.get(x, sys.maxint), -1*friendId_friend[x].mutuals))
	friendQueue.sort(key=lambda x: (friendId_streamrank.get(x.id, sys.maxint), -1*x.mutuals))

	user = getUserDb(conn, userId)
	insertCount = 0
	for i, friend in enumerate(friendQueue):
		#friend = friendId_friend[friendId]
		#friendName, mutuals = friendId_friend[friendId]

		if (readFriendStream):
			logging.info("reading friend stream %d/%d (%s)", i, len(friendQueue), friend.id)
			try:
				scFriend = readStreamParallel(friend.id, tok, STREAM_NUM_DAYS, STREAM_CHUNK_DAYS, NUM_JOBS)
			except Exception:
				logging.warning("error reading stream for %d", friend.id)
				continue
			logging.debug('got %s', str(scFriend))
			e = EdgeSC2(user, friend, sc, scFriend)
		else:
			e = EdgeSC1(user, friend, sc)
		logging.debug('edge %s', str(e))
		e.toDb(conn)
		insertCount += 1		

		updateUserDb(conn, friend, None, tok)

	updateUserDb(conn, user, tok, None)

	conn.commit()
	return insertCount

def getFriendRanking(conn, userId, includeOutgoing=True):
	edgesDb = getFriendEdgesDb(conn, userId, includeOutgoing)

	#friendId_edge = dict([ (e.id2, e) for e in edgesDb ])
	#logging.info("have %d edges", len(friendId_edge))
	
	logging.info("have %d edges", len(edgesDb))

	ipl = max([ e.inPostLikes for e in edgesDb ] + [None])
	ipc = max([ e.inPostComms for e in edgesDb ] + [None])
	isl = max([ e.inStatLikes for e in edgesDb ] + [None])
	isc = max([ e.inStatComms for e in edgesDb ] + [None])		
	opl = max([ e.outPostLikes for e in edgesDb ] + [None]) if (includeOutgoing) else None
	opc = max([ e.outPostComms for e in edgesDb ] + [None]) if (includeOutgoing) else None
	osl = max([ e.outStatLikes for e in edgesDb ] + [None]) if (includeOutgoing) else None
	opc = max([ e.outStatComms for e in edgesDb ] + [None]) if (includeOutgoing) else None
	mut = max([ e.mutuals for e in edgesDb ] + [None])
	
	#friendId_score = dict([ [e.secondary.id, e.prox(ipl, ipc, isl, isc, opl, opc, osl, opc, mut)] for e in edgesDb.values() ])

	friendTups = []
	#for friendId, score in sorted(friendId_score.items(), key=lambda x: x[1], reverse=True):
	#	edge = friendId_edge[friendId]
	#	friendTups.append((friendId, friendFname, friendLname, score))
		# gender
		# age
		# location
		# proximity level
	for edge in sorted(edgesDb, key=lambda x: x.prox(ipl, ipc, isl, isc, opl, opc, osl, opc, mut), reverse=True):
		score = edge.prox(ipl, ipc, isl, isc, opl, opc, osl, opc, mut)
		friend = edge.secondary
		friendTups.append((friend.id, friend.fname, friend.lname, friend.gender, friend.age, score))
	return friendTups

def getFriendRankingCrawl(conn, userId, tok, includeOutgoing):
	# n.b.: this kicks off a full crawl no matter what the include param!

	# first, do a partial crawl for new friends
	newCount = updateFriendEdgesDb(conn, userId, tok, readFriendStream=False, overwrite=False)

	# then, kick off a full crawl in a subprocess
	#zzz pid = subprocess.Popen(["python", "run_crawler.py", userId, tok, 1, 0]).pid

	edgeCountPart = len(getFriendEdgesDb(conn, userId, includeOutgoing=False))
	edgeCountFull = len(getFriendEdgesDb(conn, userId, includeOutgoing=True))

	if (includeOutgoing) and (edgeCountPart < 2*edgeCountFull):
		return getFriendRanking(conn, userId, includeOutgoing=True)
	else:
		return getFriendRanking(conn, userId, includeOutgoing=False)




def readStreamParallel(userId, token, numDays=100, chunkSizeDays=20, jobs=4, timeout=60):
	logging.debug("readStreamParallel(%s, %s, %d, %d, %d)" % (userId, token[:10] + "...", numDays, chunkSizeDays, jobs))

	intervals = [] # (ts1, ts2)
	chunkSizeSecs = chunkSizeDays*24*60*60
	tsNow = int(time.time())
	tsStart = tsNow-numDays*24*60*60
	for ts1 in range(tsStart, tsNow, chunkSizeSecs):
		ts2 = min(ts1 + chunkSizeSecs, tsNow)
		intervals.append((ts1, ts2))
	scChunks = Parallel(n_jobs=jobs)(delayed(readStreamChunk)(userId, token, ts1, ts2) for ts1, ts2 in intervals)
			
	logging.debug("%d chunk results for user %s", len(scChunks), userId)
	sc = StreamCounts(userId)
	for i, scChunk in enumerate(scChunks):
		logging.debug("chunk %d %s" % (i, str(scChunk)))
		sc += scChunk
	return sc
	
def readStreamChunk(userId, token, ts1, ts2, timeout=60):
	logging.debug("readStreamChunk(%s, %s, %d, %d)" % (userId, token[:10] + "...", ts1, ts2))

	queryJsons = []
	streamLabel = "stream"
	queryJsons.append('"%s":"%s"' % (streamLabel, urllib.quote_plus(FQL_STREAM_CHUNK % (userId, ts1, ts2))))
	streamRef = "#" + streamLabel
	queryJsons.append('"postLikes":"%s"' % (urllib.quote_plus(FQL_POST_LIKES % (streamRef))))
	queryJsons.append('"postComms":"%s"' % (urllib.quote_plus(FQL_POST_COMMS % (streamRef))))
	queryJsons.append('"statLikes":"%s"' % (urllib.quote_plus(FQL_STAT_LIKES % (streamRef))))
	queryJsons.append('"statComms":"%s"' % (urllib.quote_plus(FQL_STAT_COMMS % (streamRef))))
	queryJson = '{' + ','.join(queryJsons) + '}'
	#sys.stderr.write(queryJson + "\n\n")

	url = 'https://graph.facebook.com/fql?q=' + queryJson + '&format=json&access_token=' + token	
	#sys.stderr.write(url + "\n\n")

	try:
		responseFile = urllib2.urlopen(url, timeout=60)
	except Exception as e:
		logging.warning("error reading stream chunk for user %s (%s - %s): %s\n" % (userId, time.strftime("%m/%d", time.localtime(ts1)), time.strftime("%m/%d", time.localtime(ts2)), str(e)))
		return StreamCounts(userId)
	responseJson = json.load(responseFile)
	#sys.stderr.write("responseJson: " + str(responseJson)[:1000] + "\n\n")

	lab_recs = {}
	for entry in responseJson['data']:
		label = entry['name']
		records = entry['fql_result_set']
		#sys.stderr.write(label + ": " + str(records) + "\n\n")
		lab_recs[label] = records
	#return lab_recs
	pLikeIds = [ r['user_id'] for r in lab_recs['postLikes'] ]
	pCommIds = [ r['fromid'] for r in lab_recs['postComms'] ]
	sLikeIds = [ r['user_id'] for r in lab_recs['statLikes'] ]
	sCommIds = [ r['fromid'] for r in lab_recs['statComms'] ]
	sc = StreamCounts(userId, lab_recs['stream'], pLikeIds, pCommIds, sLikeIds, sCommIds)
	return sc
	



USER_TUPS = [
		(500876410, 'rayid', 'AAABlUSrYhfIBAFkDiI9l4ZBj7hKyTywQ1WkZCkw5uiWfZAUFKh73glIsEcgS390CQas9Ya8vZAMNMUnqdZCR3EhgX3ImLRF0Xy64zspM0DQZDZD'),
		(1546335889, 'tim', 'AAABlUSrYhfIBAMEo3RepupV7S9VjEjfFYxNZBrMQxutJ6ygidtFHafNwxz4ZA6m5Up4qQNIQkPk35EOAMeBZApZC1oZBKRtAlqREiCHYE1QZDZD'),
		(6963, 'michelangelo', 'AAABlUSrYhfIBAA7QmZBaEotpI4KRtTqgpMXgmG4qr76qAHH4mAzNSyCwjH6kgZCvAo99fg0SZCZAnYBZCq3IAnFaq8GjV1ZCkZD'),
		(1726740242, '---', 'AAABlUSrYhfIBAJZBjFh2ZBbgbY2O70pt0rrV13n6rYn4ZC4B7M5Hxrq6Yp64sOrAnEvjtFxmki59GaBBP7bzHkAsDEgwwtRwSUjFkElWgZDZD'),
		(727085031, '---', 'AAABlUSrYhfIBAJ8mFpQSectZAPUqRoTy38Byl7nojMscxMEi66H4qKASkUNSSI1h8RZB9ubS5SdZCiRch6ZBMOWJUQIeVlYoXdzBdUs7AQZDZD'),
		(100000530413808, '---', 'AAABlUSrYhfIBANj7nxOLFLqmUY4VG1ElRbK88p55lVZCKgYZAwrJKI5kA6rZCyT2e7f78xtuMG63BN4nUmXiwIn5dZBL4wFGj1u4Tg3UewZDZD'),
		(1193661144, '---', 'AAABlUSrYhfIBAEwdWSxjofpM5lRDkG0EC8sKJz1fYzhoDjjZCPUvDiWVywHxW6aL9RucWraGtkc2WmNBrdzdcUS1hKjYZA5iqe0STKowZDZD'),
		(100000226411771, '---', 'AAABlUSrYhfIBAP73x86UbRcKuE4WAmR0IsaCwyNvPMukxhBsKWcuzP8JycYsZChug1lgAXDBjG2rmoualRewXjePt2VqL22yZCIgiiRQZDZD'),
		(1130651020, '---', 'AAABlUSrYhfIBAAP2ZBe5zaWQnhUqxZBdbwjQYcjlLIGdukyjEHZAbg76vRwAP3mD3s44YpefZBv4ZBBQB8wcaqiNpUpqZBpCevqXVngYrILwZDZD'),
		(676731154, '---', 'AAABlUSrYhfIBANWAZA6Sb6h81iPS5vnFLObxnsnlXQOt9ZBx2RqizTWJWUeX56YWTCCmETtT7cT5VtK6T1KM14EFLVZAV8XYoPuRqncnwZDZD'),
		(100004360602886, '---', 'AAABlUSrYhfIBAHgiPdXaPLnuZAkzDo8WtDhZCQxYAyHKUOhoGNGvRZCZAr34rl1qxytTpzFCw0tEZAJ5kP2rbFrhVeI9waWtZBrNHWlhzqowZDZD'),
		(1036154377, '---', 'AAABlUSrYhfIBAOZBSIsGZAe8pm2Wj2VXPpwxOU7T8LZAYGpMjPaFZBNTCdBDEnPfUBOZAE1tzEN6bC2sBiZAaE7muSZA1laQRtrY0OWpYDKSoehhmKhJ6DO'),
		(635379288, '---', 'AAABlUSrYhfIBAFbBjEFI4LKfC0u77zeIY7h8IpopNDiPAGFsJ5ZCskgTEVXiInob6UexzDcVJ5cJ1fUXd7QGtsZAHHiDCdXiRcZCZB5D9gZDZD'),
		(27222909, '---', 'AAABlUSrYhfIBAFseiI3WPjNvJQN9SvraBwex6LkDU8HzXzw3uuWzb4wcFqInhiJVEZCV68ounBefDFuh4m5DKT224IDi2fO064ojGEwZDZD'),
		(1008191, '---', 'AAABlUSrYhfIBAGCdhhyKwiZBZBFMjVDcinCgdZBEsXSPBwsAXuiGbMu5BZACgQP6TyaRrDoxFHLB5EOT00fZCVKjQNLB6heAZD'),
		(543580444, '---', 'AAABlUSrYhfIBAB2z6DMbVu0oQdUuj46rlpPhNXaCzmdU1hZAXUdr8Ox3Gfli1mBJZB7gVX3X5e6wWShDWjWNrJAc0Jp3A3hpZC35ZAl82AZDZD'),
		(840880135, '---', 'AAABlUSrYhfIBAOnHL8ZAsiQvyTww0hEXLdx6pZCww3rj7IwAEbPgqP2KgJQ31uIig9ZB1iV2mVfIp8maARYzW0z46AlHi2iOozo1ltNwwZDZD'),
		(1487430149, '---', 'AAABlUSrYhfIBAE5ZC9GYWatTd22qouQd3NkWg9DBJZAHoV1MDwnkPWOVEOJc0cz2TJihMZBfD9l0ZBNnoBJNcR0K9uJEWeUNb1VJjBZAJ2gZDZD'),
		(100001694456083, '---', 'AAABlUSrYhfIBANwo8ghIOfscJkpWgZARHZCe0qWWZAE2U7PWvf9ZB1Tg0jnZBg7DvUUmZBk9QQZA1mZAmfm9tnHeXZAGpE36XHQ40zHXfN9p55gZDZD'),
		(1509232539, '---', 'AAABlUSrYhfIBAFOpiiSrYlBxIvCgQXMhPPZCUJWM70phLO4gQbssC3APFza3kZCMzlgcMZAkmTjZC9UACIctzDD4pn2ulXkZD'),
		(1623041802, '---', 'AAABlUSrYhfIBABinXNRPLyjW6bSWKbQZAT6X2XyBkov5oo1JWc8pqHZCgR775kLwX6k7KGKxDKwVSRPGh0K80yvqIEEUBDIfsb9C7KpgZDZD'),
		(1176046827, '---', 'AAABlUSrYhfIBADWM3erqRb4p3lGZBwCT6apifRGGuXHz8ZC1DUblK7GxGXDG1qa4QPBiTdVsvg19HqDEnxbNzZCGXqU1LbZCbk3Ed2Hz0AZDZD'),
		(1586985595, '---', 'AAABlUSrYhfIBAJpZBogkxZANKb6BVgIo371SaCrZCRSqtmQXMKtu0GML3mUdbXW1sTiBvWX7fZAyj1XhUG13AxHAd9XmuCuVVMD6Kekt3gZDZD'),
		(100004262284455, '---', 'AAABlUSrYhfIBAAd7OQabTURjCrRcLj7m0FUZBLvP441scgZB5lxIZARApMdZBpkBOzy8lz0grwo99n8QWoRBjaEXmHn8bISdqjbC7OqwsAZDZD'),
		(1320023169, '---', 'AAABlUSrYhfIBAJ2DRmZAlyab8QmpACPYdthZAZCUwyKHEYURZBT4UMDFScAQn2uVuTnjuDVY0e9MVZBZBCWoBpr8Wm8DUYnUaxO1AAN7P3BgZDZD'),
		(100001558181442, '---', 'AAABlUSrYhfIBAMyMCuZCl3J8ZAiAEYmaX9nIxrhR4xXnI6pt70slY59QydSd53Va6oJk9ser19rxbwjIjtJa2AcEpMt6CT8hcO0KRZCNQZDZD'),
		(100000066778288, '---', 'AAABlUSrYhfIBAJXn2nzhSWS9G1BlHZCZCyd7Ymow4Q31m6z10KPIVx7WYBexxIcXY2RtJbxE56V6IJB2Wbu8Rqkpb0TPybiPhWBokYkgN9z8NZBaaRZB'),
		(1556426182, '---', 'AAABlUSrYhfIBAGZCAztEoD04VgnYZAhSdBvlsuU0NObIVoV8vwlipV5XmZAcp92ZCbevNo9ZArSyRaPWBv0ZCSSWoCZCqAgMXXZC02c99Iln6AZDZD')
	]




#####################################################

if (__name__ == '__main__'):
	

	if (len(sys.argv) > 1):
		users = [ int(u) for u in sys.argv[1:] ]
	else:	
		users = [ t[0] for t in USER_TUPS ]

	user_info = dict([ (t[0], (t[1], t[2])) for t in USER_TUPS ])

	conn = ReadStreamDb.getConn()

	for i, userId in enumerate(users):
		nam, tok = user_info[userId]

		includeOutgoing = True

		user = getUserFb(userId, tok)
		updateUserDb(conn, user, tok, None)

		newCount = updateFriendEdgesDb(conn, userId, tok, readFriendStream=includeOutgoing, overwrite=False)
		logging.debug("inserted %d new edges\n" % newCount)

		friendTups = getFriendRanking(conn, userId, includeOutgoing) # id, fname, lname, gender, age, score

		#friendId_friendName = getNamesDb(conn, [ t[0] for t in friendTups ])

		for fbid, fname, lname, gender, age, score in friendTups:
			name = fname + " " + lname
			sys.stderr.write("friend %20s %32s %s %.4f\n" % (fbid, name, "", score))





 
