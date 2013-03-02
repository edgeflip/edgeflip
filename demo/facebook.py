#!/usr/bin/python
import sys
import datetime
import urllib
import urllib2
import urlparse
import json
import logging
import threading
import time
import Queue
from collections import defaultdict
import datastructs
from config import config
from contextlib import closing




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
		with closing(urllib2.urlopen(url, timeout=60)) as responseFile:
			responseJson = json.load(responseFile)
	except (urllib2.URLError, urllib2.HTTPError) as e: 
		logging.info("error opening url %s: %s" % (url, e.reason))
		try:
			# If we actually got an error back from a server, should be able to read the message here
			logging.error("returned error was: %s" % e.read())
		except:
			pass
		raise

	return responseJson

def extendTokenFb(token):
	url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=' + str(config['app_id']) + '&client_secret=' + config['app_secret'] + '&fb_exchange_token=' + token

	# Unfortunately, FB doesn't seem to allow returning JSON for new tokens, 
	# even if you try passing &format=json in the URL.
	try:
		with closing(urllib2.urlopen(url, timeout=60)) as responseFile:
			responseDict = urlparse.parse_qs(responseFile.read())
#			newToken = responseStr.split('=')[1].split('&')[0]
#			expiresIn = responseStr.split('=')[2]
			newToken = responseDict['access_token'][0]
			expiresIn = responseDict['expires'][0]
			logging.debug("Extended access token %s expires in %s seconds." % (newToken, expiresIn))
	except (urllib2.URLError, urllib2.HTTPError, IndexError, KeyError) as e:
		logging.info("error extending token %s: %s" % (token, str(e)))
		try:
			# If we actually got an error back from a server, should be able to read the message here
			logging.error("returned error was: %s" % e.read())
		except:
			pass
		raise

	return newToken

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
	sc = ReadStreamCounts(userId, tok, config['stream_days_in'], config['stream_days_chunk_in'], config['stream_threadcount_in'], loopTimeout=config['stream_read_timeout_in'], loopSleep=config['stream_read_sleep_in'])
	logging.debug('got %s', str(sc))

	# sort all the friends by their stream rank (if any) and mutual friend count
	friendId_streamrank = dict(enumerate(sc.getFriendRanking()))
	logging.debug("got %d friends ranked", len(friendId_streamrank))
	friendQueue.sort(key=lambda x: (friendId_streamrank.get(x.id, sys.maxint), -1*x.mutuals))

	# Facebook limits us to 600 calls in 600 seconds, so we need to throttle ourselves
	# relative to the number of calls we're making (the number of chunks) to 1 call / sec.
	friendSecs = config['stream_days_out'] / config['stream_days_chunk_out']

	edges = []
	user = getUserFb(userId, tok)
	for i, friend in enumerate(friendQueue):
		if (requireOutgoing):
			logging.info("reading friend stream %d/%d (%s)", i, len(friendQueue), friend.id)
			try:
				scFriend = ReadStreamCounts(friend.id, tok, config['stream_days_out'], config['stream_days_chunk_out'], config['stream_threadcount_out'], loopTimeout=config['stream_read_timeout_out'], loopSleep=config['stream_read_sleep_out'])
			except Exception as ex:
				logging.warning("error reading stream for %d: %s" % (friend.id, str(ex)))
				continue
			logging.debug('got %s', str(scFriend))
			e = datastructs.EdgeSC2(user, friend, sc, scFriend)
		else:
			e = datastructs.EdgeSC1(user, friend, sc)
		edges.append(e)
		logging.debug('edge %s', str(e))

		# Throttling for Facebook limits
		# If this friend took fewer seconds to crawl than the number of chunks, wait that
		# additional time before proceeding to next friend to avoid getting shut out by FB.
		# __NOTE__: could still run into trouble there if we have to do multiple tries for several chunks.
		if (readStreamCallback.requireOutgoing):
			secsLeft = friendSecs - timFriend.elapsedSecs()
			if (secsLeft > 0):
				logging.debug("Nap time! Waiting %d seconds..." % secsLeft)
				time.sleep(secsLeft)


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
	def __init__(self, userId, token, numDays=100, chunkSizeDays=20, threadCount=4, timeout=60, loopTimeout=10, loopSleep=0.1):
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

		numChunks = numDays / chunkSizeDays # How many chunks should we get back?

		# load the queue
		chunkSizeSecs = chunkSizeDays*24*60*60
		tsNow = int(time.time())
		tsStart = tsNow-numDays*24*60*60
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
			logging.info("ctrl-c, kill 'em all")
			for t in threads:
				t.kill_received = True
			tc = len([ t for t in threads if t.isAlive() ])
			logging.debug("now have %d threads" % (tc))

		logging.debug("%d threads still alive after loop" % (len(threads)))
		#for t in threads:
		#	t.kill_received = True		
		#tc = len([ t for t in threads if t.isAlive() ])
		#logging.debug("now have %d threads" % (tc))
	
		logging.debug("%d chunk results for user %s", len(scChunks), userId)

		badChunkRate = 1.0*(numChunks - len(scChunks)) / numChunks
		if (badChunkRate >= config['bad_chunk_thresh']):
			raise BadChunksError("Aborting ReadStreamCounts for %s: bad chunk rate exceeded threshold of %d" % (userId, config['bad_chunk_thresh']))

		sc = StreamCounts(userId) # is this left over from something? I don't think it's used... --Kit
		for i, scChunk in enumerate(scChunks):
			logging.debug("chunk %d %s" % (i, str(scChunk)))
			self.__iadd__(scChunk)
		logging.debug("ReadStreamCounts(%s, %s, %d, %d, %d) done %s" % (userId, token[:10] + "...", numDays, chunkSizeDays, threadCount, tim.elapsedPr()))

#zzz
#import gc

class ThreadStreamReader(threading.Thread):
	def __init__(self, userId, token, queue, results, lifespan):
		threading.Thread.__init__(self)
		self.userId = userId
		self.token = token
		self.queue = queue
		self.results = results
		self.lifespan = lifespan

	def run(self):
		timeStop = time.time() + self.lifespan
		logging.debug("thread %s starting" % self.name)
		timThread = datastructs.Timer()
		goodCount = 0
		errCount = 0
		while (time.time() < timeStop):
			try:
				ts1, ts2, qcount = self.queue.get_nowait()
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

			# Can be useful, but sure prints out a lot!
			# logging.debug("url from %s, interval (%s - %s): %s" % (self.userId, time.strftime("%m/%d", time.localtime(ts1)), time.strftime("%m/%d", time.localtime(ts2)), url)) 

			#try:
			#	req = urllib2.Request(url)
			#	with closing(urllib2.urlopen(req, timeout=60)) as responseFile:
			#		responseJson = json.load(responseFile)
			#except Exception as e:
			#	logging.error("error reading stream chunk for user %s (%s - %s): %s\n" % (self.userId, time.strftime("%m/%d", time.localtime(ts1)), time.strftime("%m/%d", time.localtime(ts2)), str(e)))
			#	self.queue.task_done()
			#	self.queue.put((ts1, ts2))
			#	continue

			req = urllib2.Request(url)
			try:
				responseFile = urllib2.urlopen(req, timeout=60)
			except Exception as e:
				logging.error("error reading stream chunk for user %s (%s - %s): %s" % (self.userId, time.strftime("%m/%d", time.localtime(ts1)), time.strftime("%m/%d", time.localtime(ts2)), str(e)))
				#try:
				#	responseFile.fp._sock.recv = None
				#except: # in case it's not applicable, ignore this.
				#	pass
				try:
					# If we actually got an error back from a server, should be able to read the message here
					logging.error("returned error was: %s" % e.read())
				except:
					pass
				errCount += 1
				self.queue.task_done()
				qcount += 1
				if (qcount < config['stream_read_trycount']):
					self.queue.put((ts1, ts2, qcount))
				continue

			responseJson = json.load(responseFile)
			responseFile.close()

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

			goodCount += 1

			self.results.append(sc)
			self.queue.task_done()
		
		else: # we've reached the stop limit
			logging.debug("thread %s reached lifespan, exiting" % (self.name))

		logging.debug("thread %s finishing with %d/%d good (took %s)" % (self.name, goodCount, (goodCount + errCount), timThread.elapsedPr()))

class BadChunksError(Exception):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return self.msg
