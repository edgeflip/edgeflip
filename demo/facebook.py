#!/usr/bin/python
import sys
import datetime
import urllib
import urllib2
import json
import logging
import threading
import time
import Queue
from collections import defaultdict
import datastructs
from config import config




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
#zzz perhaps this will tighten these up: http://facebook.stackoverflow.com/questions/10836965/get-posts-made-by-facebook-friends-only-on-page-through-graphapi/10837566#10837566

def dateFromFb(dateStr):
	if (dateStr):
		dateElts = dateStr.split('/')
		if (len(dateElts) == 3): 
			m, d, y = dateElts
			return datetime.date(int(y), int(m), int(d))
	return None

def getUrlFb(url):
	try:
		with urllib2.urlopen(url, timeout=60) as responseFile:
			responseJson = json.load(responseFile)
	except (urllib2.URLError, urllib2.HTTPError) as e: 
		logging.info("error opening url %s: %s" % (url, e.reason))
		raise

	return responseJson

def getFriendsFb(userId, token):
	tim = datastructs.Timer()
	logging.debug("getting friends for %d" % userId)
	fql = """SELECT uid, first_name, last_name, sex, birthday_date, current_location, mutual_friend_count FROM user WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = %s)""" % (userId)
	url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=' + token	
	responseJson = getUrlFb(url)
	#sys.stderr.write("responseJson: " + str(responseJson) + "\n\n")

	friends = []
	for rec in responseJson['data']:
		city = rec['current_location'].get('city') if (rec.get('current_location') is not None) else None
		state = rec['current_location'].get('state') if (rec.get('current_location') is not None) else None
		f = datastructs.FriendInfo(userId, rec['uid'], rec['first_name'], rec['last_name'], rec['sex'], dateFromFb(rec['birthday_date']), city, state, rec['mutual_friend_count'])
		friends.append(f)
	logging.debug("returning %d friends for %d (%s)" % (len(friends), userId, tim.elapsedPr()))
	return friends

def getUserFb(userId, token):
	fql = """SELECT uid, first_name, last_name, sex, birthday_date, current_location FROM user WHERE uid=%s""" % (userId)
	url = 'https://graph.facebook.com/fql?q=' + urllib.quote_plus(fql) + '&format=json&access_token=' + token	
	responseJson = getUrlFb(url)
	rec = responseJson['data'][0]
	city = rec['current_location'].get('city') if (rec.get('current_location') is not None) else None
	state = rec['current_location'].get('state') if (rec.get('current_location') is not None) else None
	user = datastructs.UserInfo(rec['uid'], rec['first_name'], rec['last_name'], rec['sex'], dateFromFb(rec['birthday_date']), city, state)
	return user

def getFriendEdgesFb(userId, tok, requireOutgoing=False, skipFriends=set()):

	logging.debug("getting friend edges from FB for %d" % userId)
	tim = datastructs.Timer()

	friends = getFriendsFb(userId, tok)
	
	logging.debug("got %d friends total", len(friends))
	
	friendQueue = [f for f in friends if f.id not in skipFriends]

	logging.info('reading stream for user %s, %s', userId, tok)
	sc = ReadStreamCounts(userId, tok, config['stream_days'], config['stream_days_chunk'], config['stream_threadcount'])
	logging.debug('got %s', str(sc))

	# sort all the friends by their stream rank (if any) and mutual friend count
	friendId_streamrank = dict(enumerate(sc.getFriendRanking()))
	logging.debug("got %d friends ranked", len(friendId_streamrank))
	friendQueue.sort(key=lambda x: (friendId_streamrank.get(x.id, sys.maxint), -1*x.mutuals))

	edges = []
	user = getUserFb(userId, tok)
	for i, friend in enumerate(friendQueue):
		if (requireOutgoing):
			logging.info("reading friend stream %d/%d (%s)", i, len(friendQueue), friend.id)
			try:
				scFriend = ReadStreamCounts(friend.id, tok, config['stream_days'], config['stream_days_chunk'], config['stream_threadcount'])
			except Exception as ex:
				logging.warning("error reading stream for %d: %s" % (friend.id, str(ex)))
				continue
			logging.debug('got %s', str(scFriend))
			e = datastructs.EdgeSC2(user, friend, sc, scFriend)
		else:
			e = datastructs.EdgeSC1(user, friend, sc)
		edges.append(e)
		logging.debug('edge %s', str(e))

	logging.debug("got %d friend edges for %d (%s)" % (len(edges), userId, tim.elapsedPr()))

	return edges


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
	
class ReadStreamCounts(StreamCounts):
	def __init__(self, userId, token, numDays=100, chunkSizeDays=20, threadCount=4, timeout=60):
		logging.debug("ReadStreamCounts(%s, %s, %d, %d, %d)" % (userId, token[:10] + "...", numDays, chunkSizeDays, threadCount))
		tim = datastructs.Timer()
		self.id = userId
		self.stream = []
		self.friendId_postLikeCount = defaultdict(int)
		self.friendId_postCommCount = defaultdict(int)
		self.friendId_statLikeCount = defaultdict(int)
		self.friendId_statCommCount = defaultdict(int)

		tsQueue = Queue.Queue() # fill with (t1, t2) pairs
		scChunks = [] # list of sc obects holding results

		# load the queue
		intervals = [] # (ts1, ts2)
		chunkSizeSecs = chunkSizeDays*24*60*60
		tsNow = int(time.time())
		tsStart = tsNow-numDays*24*60*60
		for ts1 in range(tsStart, tsNow, chunkSizeSecs):
			ts2 = min(ts1 + chunkSizeSecs, tsNow)
			tsQueue.put((ts1, ts2))

		# create the thread pool
		threads = []
		for i in range(threadCount):
			t = ThreadStreamReader(userId, token, tsQueue, scChunks)
			t.setDaemon(True)
			t.name = "%s-%d" % (userId, i)
			threads.append(t)
			t.start()

		timeStop = time.time() + config['stream_read_timeout']
		try:
			while (time.time() < timeStop):
				threadsAlive = []
				for t in threads:
					if t.isAlive():
						threadsAlive.append(t)
				threads = threadsAlive
				if (threadsAlive):
					time.sleep(config['stream_read_sleep'])
				else:
					break

		except KeyboardInterrupt:
			logging.info("ctrl-c, kill 'em all")
			for t in threads:
				t.kill_received = True
			tc = len([ t for t in threads if t.isAlive() ])
			logging.debug("now have %d threads" % (tc))

		logging.debug("%d threads still alive after loop" % (len(threads)))
			
		logging.debug("%d chunk results for user %s", len(scChunks), userId)

		sc = StreamCounts(userId)
		for i, scChunk in enumerate(scChunks):
			logging.debug("chunk %d %s" % (i, str(scChunk)))
			self.__iadd__(scChunk)
		logging.debug("ReadStreamCounts(%s, %s, %d, %d, %d) done %s" % (userId, token[:10] + "...", numDays, chunkSizeDays, threadCount, tim.elapsedPr()))

class ThreadStreamReader(threading.Thread):
	def __init__(self, userId, token, queue, results):
		threading.Thread.__init__(self)
		self.userId = userId
		self.token = token
		self.queue = queue
		self.results = results

	def run(self):
		while True:

			try:
				ts1, ts2 = self.queue.get_nowait()
			except Queue.Empty as e:
				break
		
			tim = datastructs.Timer()

			logging.debug("reading stream for %s, interval (%s - %s)" % (self.userId, time.strftime("%m/%d", time.localtime(ts1)), time.strftime("%m/%d", time.localtime(ts2))))

			queryJsons = []
			streamLabel = "stream"
			queryJsons.append('"%s":"%s"' % (streamLabel, urllib.quote_plus(FQL_STREAM_CHUNK % (self.userId, ts1, ts2))))
			streamRef = "#" + streamLabel
			queryJsons.append('"postLikes":"%s"' % (urllib.quote_plus(FQL_POST_LIKES % (streamRef))))
			queryJsons.append('"postComms":"%s"' % (urllib.quote_plus(FQL_POST_COMMS % (streamRef))))
			queryJsons.append('"statLikes":"%s"' % (urllib.quote_plus(FQL_STAT_LIKES % (streamRef))))
			queryJsons.append('"statComms":"%s"' % (urllib.quote_plus(FQL_STAT_COMMS % (streamRef))))
			queryJson = '{' + ','.join(queryJsons) + '}'
			#sys.stderr.write(queryJson + "\n\n")

			url = 'https://graph.facebook.com/fql?q=' + queryJson + '&format=json&access_token=' + self.token	
			#sys.stderr.write(url + "\n\n") 

			try:
				with urllib2.urlopen(url, timeout=60) as responseFile:
					responseJson = json.load(responseFile)
			except Exception as e:
				logging.error("error reading stream chunk for user %s (%s - %s): %s\n" % (self.userId, time.strftime("%m/%d", time.localtime(ts1)), time.strftime("%m/%d", time.localtime(ts2)), str(e)))
				self.queue.task_done()
				self.queue.put((ts1, ts2))
				continue

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
			sc = StreamCounts(self.userId, lab_recs['stream'], pLikeIds, pCommIds, sLikeIds, sCommIds)

			logging.debug("stream counts for %s: %s" % (self.userId, str(sc)))
			logging.debug("chunk took %s" % (tim.elapsedPr()))

			self.results.append(sc)
			self.queue.task_done()


