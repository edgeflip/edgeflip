#!/usr/bin/python
import sys
import threading
import logging
import time
import urllib
import urllib2
import json
import os
import pika
import argparse
import Queue
from collections import defaultdict
import ReadStream
import ReadStreamDb
from Config import config


logPika = logging.getLogger('pika')
logPika.setLevel(logging.CRITICAL)

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

THREAD_COUNT = 12
STREAM_NUM_DAYS = 120
STREAM_CHUNK_DAYS = 10




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
		tim = ReadStream.Timer()
		self.id = userId
		self.stream = []
		self.friendId_postLikeCount = defaultdict(int)
		self.friendId_postCommCount = defaultdict(int)
		self.friendId_statLikeCount = defaultdict(int)
		self.friendId_statCommCount = defaultdict(int)

		tsQueue = Queue.Queue() # fill with (t1, t2) pairs
		scChunks = [] # list of sc obects holding results

		# create the thread pool
		threads = []
		for i in range(threadCount):
			t = ThreadStreamReader(userId, token, tsQueue, scChunks)
			t.setDaemon(True)
			t.name = "%s-%d" % (userId, i)
			threads.append(t)
			t.start()

		# load the queue
		intervals = [] # (ts1, ts2)
		chunkSizeSecs = chunkSizeDays*24*60*60
		tsNow = int(time.time())
		tsStart = tsNow-numDays*24*60*60
		for ts1 in range(tsStart, tsNow, chunkSizeSecs):
			ts2 = min(ts1 + chunkSizeSecs, tsNow)
			tsQueue.put((ts1, ts2))

		# wait for them to finish
		#tsQueue.join()
		while len(threads) > 0:

			logging.debug("threads: " + str(threads))

			try:
				# Join all threads using a timeout so it doesn't block
				# Filter out threads which have been joined or are None

				threads = [ t.join(1) for t in threads if t is not None and t.isAlive() ]

			except KeyboardInterrupt:
				logging.info("ctrl-c, kill 'em all")
				for t in threads:
					t.kill_received = True
				tc = [ t for t in threads if t is not None and t.isAlive() ]
				logging.debug("now have %d threads" % (tc))
				
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
			tim = ReadStream.Timer()

			ts1, ts2 = self.queue.get()
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
				responseFile = urllib2.urlopen(url, timeout=60)
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


def readStreamCallback(ch, method, properties, body):
	logging.debug("got raw message %d '%s' from queue" % (readStreamCallback.messCount, body))
	readStreamCallback.messCount += 1
	elts = json.loads(body)
	#logging.debug("got message elts %s from queue" % str(elts))
	userId, tok, extra = elts
	logging.debug("received %d, %s from queue" % (userId, tok))

	try:
		user = ReadStream.getUserFb(userId, tok)
	except:
		ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
		return
	
	conn = ReadStreamDb.getConn()
	ReadStream.updateUserDb(conn, user, tok, None)
	newCount = ReadStream.updateFriendEdgesDb(conn, userId, tok, 
						readFriendStream=readStreamCallback.includeOutgoing, 
						overwriteThresh=readStreamCallback.overwriteThresh)
	logging.info("updated %d edges for user %d" % (newCount, userId))

	ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)

# globals for the callback
readStreamCallback.includeOutgoing = False
readStreamCallback.overwriteThresh = sys.maxint # never overwrite
readStreamCallback.messCount = 0


def debugCallback(ch, method, properties, body):
	sys.stderr.write("received %s from queue\n" % (str(body)))
	ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)




#####################################################

if (__name__ == '__main__'):

	parser = argparse.ArgumentParser(description='launch worker to consume download queue')
	parser.add_argument('queueName', help='name of queue with which to connect')
	parser.add_argument('crawlType', help='p(artial) or f(ull)')
	parser.add_argument('--overwrite', metavar='secs', type=int, default=sys.maxint, help='refresh existing entries older than threshold')
	args = parser.parse_args()

	if (args.crawlType.lower()[0] == 'p'):
		includeOutgoing = False
	elif (args.crawlType.lower()[0] == 'f'):
		includeOutgoing = True
	else:
		raise Exception("crawl type must be 'p' (partial) or 'f' (full)")

	overwriteThresh = args.overwrite

	#zzz
	#callbackFunc = debugCallback
	callbackFunc = readStreamCallback

	pid = os.getpid()
	logging.info("starting worker %d for queue %s" % (pid, args.queueName))

	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()

	logging.debug("check 1")
	channel.queue_declare(queue=args.queueName, durable=True)

	logging.debug("check 2")
	channel.basic_consume(callbackFunc, args.queueName)

	logging.debug("check 3")
	channel.start_consuming()

	logging.debug("check 4")





