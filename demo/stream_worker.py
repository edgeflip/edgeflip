#!/usr/bin/python
import os
import sys
import argparse
import logging
import facebook
import database
import datastructs
import time
import json
import pika

from config import config
logging.getLogger('pika').setLevel(logging.CRITICAL)



def readStreamCallback(ch, method, properties, body):
	logging.debug("[worker] got raw message %d '%s' from queue" % (readStreamCallback.messCount, body))
	readStreamCallback.messCount += 1
	elts = json.loads(body)
	#logging.debug("got message elts %s from queue" % str(elts))
	userId, tok, extra = elts
	userId = int(userId)
	logging.debug("[worker] received %d, %s from queue" % (userId, tok))
	sys.stderr.write("received %d, %s from queue\n" % (userId, tok))

	try:
		user = facebook.getUserFb(userId, tok)
	except:
		ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
		return


	logging.debug("[worker] getting friend edges from FB for %d" % userId)
	tim = datastructs.Timer()
	
	conn = database.getConn()
	curs = conn.cursor()

	database.updateUserDb(curs, user, tok, None) # Update the primary user in DB

	skipFriends = set()
	if (readStreamCallback.overwriteThresh != 0):
		# want the edges that were updated less than overwriteThresh secs ago, we'll exclude these
		updateThresh = time.time() - readStreamCallback.overwriteThresh
		edgesDb = database.getFriendEdgesDb(conn, userId, readStreamCallback.requireOutgoing, newerThan=updateThresh)
		skipFriends.update([ e.secondary.id for e in edgesDb ])

	friends = facebook.getFriendsFb(userId, tok)
	friendQueue = [f for f in friends if f.id not in skipFriends]
	logging.debug("[worker] got %d friends total; updating %d of them" % ( len(friends), len(friendQueue) ))

	logging.info('[worker] reading stream for user %s, %s', userId, tok)
	sc = facebook.ReadStreamCounts(userId, tok, config['stream_days'], config['stream_days_chunk'], config['stream_threadcount'])
	logging.debug('[worker] got %s', str(sc))

	# sort all the friends by their stream rank (if any) and mutual friend count
	friendId_streamrank = dict(enumerate(sc.getFriendRanking()))
	logging.debug("[worker] got %d friends ranked", len(friendId_streamrank))
	friendQueue.sort(key=lambda x: (friendId_streamrank.get(x.id, sys.maxint), -1*x.mutuals))

	newCount = 0
	for i, friend in enumerate(friendQueue):
		if (readStreamCallback.requireOutgoing):
			logging.info("[worker] reading friend stream %d/%d (%s)", i, len(friendQueue), friend.id)

			try:
				scFriend = facebook.ReadStreamCounts(friend.id, tok, config['stream_days'], config['stream_days_chunk'], config['stream_threadcount'])
			except Exception as ex:
				logging.warning("[worker] error reading stream for %d: %s" % (friend.id, str(ex)))
				continue
			logging.debug('[worker] got %s', str(scFriend))
			e = datastructs.EdgeSC2(user, friend, sc, scFriend)
		else:
			e = datastructs.EdgeSC1(user, friend, sc)

		database.updateUserDb(curs, e.secondary, None, tok) # Update the secondary user in DB
		database.updateFriendEdgeDb(curs, e) # Update the edge in DB
		conn.commit()

		newCount += 1
		logging.debug('[worker] edge %s', str(e))
		sys.stderr.write("\twrote edge %d/%d %d--%d %s\n" % (i, len(friendQueue)-1, e.primary.id, e.secondary.id, str(e)))

	logging.debug("[worker] updated %d friend edges for %d (took: %s)" % (newCount, userId, tim.elapsedPr()))
	sys.stderr.write("updated %d friend edges for %d (took: %s)\n" % (newCount, userId, tim.elapsedPr()))

	ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)

# globals for the callback
readStreamCallback.requireOutgoing = False
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
		readStreamCallback.requireOutgoing = False
	elif (args.crawlType.lower()[0] == 'f'):
		readStreamCallback.requireOutgoing = True
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

	channel.queue_declare(queue=args.queueName, durable=True)
	channel.basic_consume(callbackFunc, args.queueName)
	channel.start_consuming()
