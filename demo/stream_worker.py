#!/usr/bin/python
import pika
import os
import argparse
import logging
import facebook
from Config import config




def readStreamCallback(ch, method, properties, body):
	logging.debug("got raw message %d '%s' from queue" % (readStreamCallback.messCount, body))
	readStreamCallback.messCount += 1
	elts = json.loads(body)
	#logging.debug("got message elts %s from queue" % str(elts))
	userId, tok, extra = elts
	logging.debug("received %d, %s from queue" % (userId, tok))

	try:
		user = facebook.getUserFb(userId, tok)
	except:
		ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
		return
	
	conn = database.getConn()
	database.updateUserDb(conn, user, tok, None)
	newCount = database.updateFriendEdgesDb(conn, userId, tok, 
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

	channel.queue_declare(queue=args.queueName, durable=True)
	channel.basic_consume(callbackFunc, args.queueName)
	channel.start_consuming()

