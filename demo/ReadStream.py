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
import json

# try:
# 	ef_config = open('edgeflip.config', 'r')
# 	ef_dict = json.loads(ef_config.read())
# 	if (not ef_dict['outdir']):
# 		ef_dict['outdir'] = ''
# except:
# 	ef_dict = {'outdir' : ''}
# logging.basicConfig(format='%(asctime)s\t%(levelname)s\t%(message)s',
# 					filename=ef_dict['outdir']+'demo.log',
# 					level=logging.DEBUG)
from Config import config
import ReadStreamDb
import StreamReaderWorker


NUM_JOBS = 12
STREAM_NUM_DAYS = 120
STREAM_CHUNK_DAYS = 5


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
	def __init__(self, uid, first_name, last_name, sex, birthday, city, state):
		self.id = uid
		self.fname = first_name
		self.lname = last_name
		self.gender = sex

		self.birthday = birthday
		self.age = int((datetime.date.today() - self.birthday).days/365.25) if (birthday) else None

		self.city = city
		self.state = state

class FriendInfo(UserInfo):
	def __init__(self, primId, friendId, first_name, last_name, sex, birthday, city, state, mutual_friend_count):
		UserInfo.__init__(self, friendId, first_name, last_name, sex, birthday, city, state)
		self.idPrimary = primId
		self.mutuals = mutual_friend_count

def getUrlFb(url):
	try:
		responseFile = urllib2.urlopen(url, timeout=60)
	except (urllib2.URLError, urllib2.HTTPError) as e: 
		logging.info("error opening url %s: %s" % (url, e.reason))
		raise
	responseJson = json.load(responseFile)
	return responseJson


def getFriendsFb(userId, token):
	tim = Timer()
	logging.debug("getting friends for %d" % userId)
	fql = """SELECT uid, first_name, last_name, sex, birthday_date, current_location, mutual_friend_count FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = %s)""" % (userId)
	url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=' + token	
	#try:
	#	responseFile = urllib2.urlopen(url, timeout=60)
	#except urllib2.URLError, urllib2.HTTPError as e:
	#	logging.info("error opening friends url for user %s: %s" % (userId, e.reason))
	#	return None
	#responseJson = json.load(responseFile)
	responseJson = getUrlFb(url)

	#sys.stderr.write("responseJson: " + str(responseJson) + "\n\n")
	#friendIds = [ rec['uid2'] for rec in responseJson['data'] ]
	#friendTups = [ (rec['uid'], rec['name'], rec['mutual_friend_count']) for rec in responseJson['data'] ]
	#return friendTups
	friends = []
	for rec in responseJson['data']:
		city = rec['current_location'].get('city') if (rec.get('current_location') is not None) else None
		state = rec['current_location'].get('state') if (rec.get('current_location') is not None) else None
		f = FriendInfo(userId, rec['uid'], rec['first_name'], rec['last_name'], rec['sex'], dateFromFb(rec['birthday_date']), city, state, rec['mutual_friend_count'])
		friends.append(f)
	logging.debug("returning %d friends for %d (%s)" % (len(friends), userId, tim.elapsedPr()))
	return friends


def getUserFb(userId, token):
	fql = """SELECT uid, first_name, last_name, sex, birthday_date, current_location FROM user WHERE uid=%s""" % (userId)
	url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=' + token	
	#try:
	#	responseFile = urllib2.urlopen(url, timeout=60)
	#except urllib2.URLError, urllib2.HTTPError as e:
        #        logging.info("error opening user url for user %s: %s" % (userId, e.reason))
        #        return None
	#responseJson = json.load(responseFile)
	responseJson = getUrlFb(url)
	rec = responseJson['data'][0]
	city = rec['current_location'].get('city') if (rec.get('current_location') is not None) else None
	state = rec['current_location'].get('state') if (rec.get('current_location') is not None) else None
	user = UserInfo(rec['uid'], rec['first_name'], rec['last_name'], rec['sex'], dateFromFb(rec['birthday_date']), city, state)
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


def getUserDb(conn, userId):
	sql = """SELECT fbid, fname, lname, gender, birthday, city, state, token, friend_token, updated FROM users WHERE fbid=%s""" % userId
	#logging.debug(sql)
	curs = conn.cursor()
	curs.execute(sql)
	rec = curs.fetchone()
	#logging.debug(str(rec))
	fbid, fname, lname, gender, birthday, city, state, token, friend_token, updated = rec
	return UserInfo(fbid, fname, lname, gender, dateFromIso(birthday), city, state)

def getFriendEdgesDb(conn, primId, requireOutgoing=False, newerThan=0):
	if (conn is None):
		conn = ReadStreamDb.getConn()
	curs = conn.cursor()
	sql = """
			SELECT prim_id, sec_id,
					in_post_likes, in_post_comms, in_stat_likes, in_stat_comms,
					out_post_likes, out_post_comms, out_stat_likes, out_stat_comms, 
					mut_friends, updated
			FROM edges
			WHERE prim_id=? AND updated>?
	""" 
	if (requireOutgoing):
		sql += """
			AND out_post_likes IS NOT NULL 
			AND out_post_comms IS NOT NULL 
			AND out_stat_likes IS NOT NULL
			AND out_stat_comms IS NOT NULL
		"""
	curs.execute(sql, (primId, newerThan))
	eds = []
	primary = getUserDb(conn, primId)
	for pId, sId, inPstLk, inPstCm, inStLk, inStCm, outPstLk, outPstCm, outStLk, outStCm, muts, updated in curs:
		secondary = getUserDb(conn, sId)
		eds.append(Edge(primary, secondary, inPstLk, inPstCm, inStLk, inStCm, outPstLk, outPstCm, outStLk, outStCm, muts))
	return eds

def updateUserDb(conn, user, tok, tokFriend):
	# can leave tok or tokFriend blank, in that case it will not overwrite

	sql = "INSERT OR REPLACE INTO users (fbid, fname, lname, gender, birthday, city, state, token, friend_token, updated) "
	if (tok is None):
		sql += "VALUES (?, ?, ?, ?, ?, ?, ?, (SELECT token FROM users WHERE fbid=?), ?, ?)"
		params = (user.id, user.fname, user.lname, user.gender, str(user.birthday), user.city, user.state, user.id, tokFriend, time.time())
	elif (tokFriend is None):
		sql += "VALUES (?, ?, ?, ?, ?, ?, ?, ?, (SELECT friend_token FROM users WHERE fbid=?), ?)"
		params = (user.id, user.fname, user.lname, user.gender, str(user.birthday), user.city, user.state, tok, user.id, time.time())
	else:
		sql += "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
		params = (user.id, user.fname, user.lname, user.gender, str(user.birthday), user.city, user.state, tok, tokFriend, time.time())
	curs = conn.cursor()
	curs.execute(sql, params)
	conn.commit()	

def updateFriendEdgesDb(conn, userId, tok, readFriendStream=True, overwriteThresh=sys.maxint): # default behavior is never overwrite
	logging.debug("updating friend edges for %d" % userId)
	tim = Timer()
	try:
		friends = getFriendsFb(userId, tok)
	except:
		return -1

	logging.debug("got %d friends total", len(friends))

	# if we're not overwriting, see what we have saved
	if (overwriteThresh == 0):
		#friendQueue = friendId_friend.keys()
		friendQueue = friends
	else:
		# want the edges that were updated less than overwriteThresh secs ago, we'll exclude these
		updateThresh = time.time() - overwriteThresh
		edgesDb = getFriendEdgesDb(conn, userId, requireOutgoing=readFriendStream, newerThan=updateThresh)
		friendIdsPrev = set([ e.secondary.id for e in edgesDb ])
		friendQueue = [ f for f in friends if f.id not in friendIdsPrev ]

	logging.info('reading stream for user %s, %s', userId, tok)
	#sc = StreamReader.readStream(userId, tok, STREAM_NUM_DAYS, STREAM_CHUNK_DAYS, NUM_JOBS)
	sc = StreamReaderWorker.ReadStreamCounts(userId, tok, STREAM_NUM_DAYS, STREAM_CHUNK_DAYS, NUM_JOBS)

	logging.debug('got %s', str(sc))

	# sort all the friends by their stream rank (if any) and mutual friend count
	friendId_streamrank = dict(enumerate(sc.getFriendRanking()))
	logging.debug("got %d friends ranked", len(friendId_streamrank))
	#friendQueue.sort(key=lambda x: (friendId_streamrank.get(x, sys.maxint), -1*friendId_friend[x].mutuals))
	friendQueue.sort(key=lambda x: (friendId_streamrank.get(x.id, sys.maxint), -1*x.mutuals))

	user = getUserDb(conn, userId)
	insertCount = 0
	for i, friend in enumerate(friendQueue):
		if (readFriendStream):
			logging.info("reading friend stream %d/%d (%s)", i, len(friendQueue), friend.id)
			try:
				#scFriend = StreamReader.readStream(friend.id, tok, STREAM_NUM_DAYS, STREAM_CHUNK_DAYS, NUM_JOBS)
				scFriend = StreamReaderWorker.ReadStreamCounts(friend.id, tok, STREAM_NUM_DAYS, STREAM_CHUNK_DAYS, NUM_JOBS)

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

	logging.debug("updated %d friend edges for %d (%s)" % (insertCount, userId, tim.elapsedPr()))
	return insertCount

def getFriendRanking(conn, userId, requireOutgoing=True):
	edgesDb = getFriendEdgesDb(conn, userId, requireOutgoing)
	logging.info("have %d edges", len(edgesDb))

	ipl = max([ e.inPostLikes for e in edgesDb ] + [None])
	ipc = max([ e.inPostComms for e in edgesDb ] + [None])
	isl = max([ e.inStatLikes for e in edgesDb ] + [None])
	isc = max([ e.inStatComms for e in edgesDb ] + [None])		
	opl = max([ e.outPostLikes for e in edgesDb ] + [None]) if (requireOutgoing) else None
	opc = max([ e.outPostComms for e in edgesDb ] + [None]) if (requireOutgoing) else None
	osl = max([ e.outStatLikes for e in edgesDb ] + [None]) if (requireOutgoing) else None
	opc = max([ e.outStatComms for e in edgesDb ] + [None]) if (requireOutgoing) else None
	mut = max([ e.mutuals for e in edgesDb ] + [None])
	
	friendTups = []
	for edge in sorted(edgesDb, key=lambda x: x.prox(ipl, ipc, isl, isc, opl, opc, osl, opc, mut), reverse=True):
		score = edge.prox(ipl, ipc, isl, isc, opl, opc, osl, opc, mut)
		friend = edge.secondary
		friendTups.append((friend.id, friend.fname, friend.lname, friend.gender, friend.age, friend.city, friend.state, str(edge), score))
	return friendTups

def spawnCrawl(userId, tok, requireOutgoing, overwrite):
	# python run_crawler.py userId tok outgoing overwrite
	pid = subprocess.Popen(["python", config['codedir'].rstrip('/') + "/run_crawler.py", str(userId), tok, "1" if requireOutgoing else "0", "1" if overwrite else "0"]).pid
	logging.debug("spawned process %d to crawl user %d" % (pid, userId))
	return pid

def getFriendRankingBestAvail(conn, userId, threshold=0.5):
	edgeCountPart = len(getFriendEdgesDb(conn, userId, requireOutgoing=False))
	edgeCountFull = len(getFriendEdgesDb(conn, userId, requireOutgoing=True))
	if (edgeCountPart*threshold < edgeCountFull):
		return getFriendRanking(conn, userId, requireOutgoing=True)
	else:
		return getFriendRanking(conn, userId, requireOutgoing=False)




def formatSecs(secs):
	secs = int(secs)
	if (secs < 3600):
		return time.strftime("%M:%S", time.gmtime(secs))
	elif (secs < 86400):
		return time.strftime("%H:%M:%S", time.gmtime(secs))
	else:
		return str(secs/86400) + ":" + time.strftime("%H:%M:%S", time.gmtime(secs%86400))
class Timer:
	def __init__(self):
		self.start = time.time()
	def reset(self):
		self.start = time.time()
	def elapsed(self):
		return time.time() - self.start
	def elapsedPr(self):
		return formatSecs(time.time() - self.start)
	def stderr(self, txt=""):
		sys.stderr.write(self.elapsedPr() + " " + txt + "\n")
tim = Timer()
def elapsedPr():
	return tim.elapsedPr()







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


	ReadStreamDb.dbSetup()

	conn = ReadStreamDb.getConn()

	for i, userId in enumerate(users):
		nam, tok = user_info[userId]

		requireOutgoing = True

		try:
			user = getUserFb(userId, tok)
		except:	
			logging.info("error processing user %d" % userId)
			continue
		updateUserDb(conn, user, tok, None)

		newCount = updateFriendEdgesDb(conn, userId, tok, readFriendStream=requireOutgoing, overwrite=True)
		logging.debug("inserted %d new edges\n" % newCount)

		friendTups = getFriendRanking(conn, userId, requireOutgoing) # id, fname, lname, gender, age, desc, score
		for fbid, fname, lname, gender, age, desc, score in friendTups:
			name = fname + " " + lname
			sys.stderr.write("friend %20s %32s %s %.4f\n" % (fbid, name, "", score))





 
