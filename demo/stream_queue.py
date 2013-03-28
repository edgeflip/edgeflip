#!/usr/bin/python
import sys
import pika
import argparse
import json
import logging
import config as conf
config = conf.readJson(includeDefaults=True)
logging.getLogger('pika').setLevel(logging.CRITICAL)


def createQueue(queueName):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue=queueName, durable=True)
	connection.close()

def deleteQueue(queueName):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_delete(queue=queueName)
	connection.close()

def resetQueue(queueName):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_delete(queue=queueName)
	channel.queue_declare(queue=queueName, durable=True)
	connection.close()

def loadQueue(queueName, entries, transFunc=lambda x: x):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.queue_declare(queue=queueName, durable=True)
	props = pika.BasicProperties(delivery_mode=2) # make message persistent
	publishCount = 0
	for entry in entries:
		entryTrans = transFunc(entry)
		entryJson = json.dumps(entryTrans)
		channel.basic_publish(exchange='', routing_key=queueName, body=entryJson, properties=props)		
		publishCount += 1
	connection.close()
	return publishCount

def loadQueueFile(queueName, loadName):
	with open(loadName, 'r') as infile:
		return loadQueue(queueName, infile, lambda line: json.loads(line.rstrip("\n")))

def getQueueSize(queueName):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	count = channel.queue_declare(queue=queueName, durable=True, passive=True).method.message_count
	return count




##############################################

if (__name__ == '__main__'):

	parser = argparse.ArgumentParser(description='create/delete/load download queue')
	parser.add_argument('queueName', help='name of queue with which to connect')
	parser.add_argument('--load', metavar='infile', help='load queue entries from file')
	parser.add_argument('--create', action='store_true', help='create the queue')
	parser.add_argument('--delete', action='store_true', help='delete the queue')
	parser.add_argument('--reset', action='store_true', help='empty the queue')
	args = parser.parse_args()

	if (args.delete):
		deleteQueue(args.queueName)
	if (args.create):
		createQueue(args.queueName)
	if (args.reset):
		resetQueue(args.queueName)
	if (args.load):
		loadQueueFile(args.queueName, args.load)	
		#with open(args.load, 'r') as infile:
		#	loadQueue(args.queueName, infile, lambda line: json.loads(line.rstrip("\n")))

	sys.stderr.write("queue has %d elements\n" % getQueueSize(args.queueName))

