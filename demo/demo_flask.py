#!/usr/bin/python
import flask
from flask import Flask, render_template
import ReadStream
import ReadStreamDb
import StreamReaderQueue
import sys
import json
import time

from Config import config


app = Flask(__name__)


@app.route("/", methods=['POST', 'GET'])
def home():
	return "One day, I'll write a page with links... for now, you get this."

@app.route('/demo')
@app.route('/button')
@app.route('/all_the_dude_ever_wanted')
def button_man():
	return render_template('frame_wide.html')

@app.route('/demo_faces', methods=['POST'])
def face_it():
	sys.stderr.write("flask.request.json: %s\n" % (str(flask.request.json)))

	fbid = flask.request.json['fbid']
	tok = flask.request.json['token']
	num = int(flask.request.json['num'])

	conn = ReadStreamDb.getConn()
	user = ReadStream.getUserFb(fbid, tok)
	ReadStream.updateUserDb(conn, user, tok, None)

 	# first, do a partial crawl for new friends
	newCount = ReadStream.updateFriendEdgesDb(conn, fbid, tok, readFriendStream=False)

	# now, spawn a full crawl in the background
	StreamReaderQueue.loadQueue(config['queue'], [(fbid, tok, "")])

	friendTups = ReadStream.getFriendRankingBestAvail(conn, fbid, threshold=0.5)
	friendDicts = []

	for i, t in enumerate(friendTups):
		fd = { 'rank':i, 'id':t[0], 'name':" ".join(t[1:3]), 'gender':t[3], 'age':t[4],  'desc':t[5], 'score':"%.4f"%float(t[6]), 'fname':t[1], 'lname':t[2] }
		for c, count in enumerate(t[2].split()):
			fd['count' + str(c)] = count
		friendDicts.append(fd)

	for fd in friendDicts:
		sys.stderr.write(str(fd) + "\n")

	# Apply control panel targeting filters
	filteredDicts = filter_friends(friendDicts)

	faceFriends = filteredDicts[:6]
	numFace = len(faceFriends)
	allFriends = filteredDicts[:25]
	ret = render_template('faces_table_wide.html', face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace)

	return ret


@app.route('/rank')
def rank_demo():
	return render_template('rank_demo.html')

@app.route('/rank_faces', methods=['POST'])
def rank_faces():
	import time
	
	fbid = flask.request.json['fbid']
	tok = flask.request.json['token']
	rankfn = flask.request.json['rankfn']

	conn = ReadStreamDb.getConn()
	user = ReadStream.getUserFb(fbid, tok)
	ReadStream.updateUserDb(conn, user, tok, None)

 	# first, do a partial crawl for new friends
	newCount = ReadStream.updateFriendEdgesDb(conn, fbid, tok, readFriendStream=False)

	if (rankfn.lower() == "px4"):

		# now, spawn a full crawl in the background
		StreamReaderQueue.loadQueue(config['queue'], [(fbid, tok, "")])
 		friendTups = ReadStream.getFriendRanking(conn, fbid, includeOutgoing=False)

	else:
 		friendTups = ReadStream.getFriendRanking(conn, fbid, includeOutgoing=True)

	friendDicts = []
	for i, t in enumerate(friendTups):
		fd = { 'rank':i, 'id':t[0], 'name':" ".join(t[1:3]), 'gender':t[3], 'age':t[4],  'desc':t[5].replace('None', '&Oslash;'), 'score':"%.4f"%float(t[6]) }
		friendDicts.append(fd)

	# Apply control panel targeting filters
	filteredDicts = filter_friends(friendDicts)

	ret = render_template('rank_faces.html', face_friends=filteredDicts)
	return ret
	

@app.route('/suppress', methods=['POST'])
def suppress():
	userid = flask.request.json['userid']
	appid = flask.request.json['appid']
	content = flask.request.json['content']
	oldid = flask.request.json['oldid']

	newid = flask.request.json['newid']
	fname = flask.request.json['fname']
	lname = flask.request.json['lname']

	# SEND TO DB: userid suppressed oldid for appid+content

	if (newid != ''):
		return render_template('new_face.html', id=newid, fname=fname, lname=lname)
	else:
		return ''


############################ CONTROL PANEL #############################

@app.route("/cp", methods=['POST', 'GET'])
@app.route("/control_panel", methods=['POST', 'GET'])
def cp():
	config_dict = {}
	try:
		cf = open(config['outdir']+'target_config.json', 'r')
		config_dict = json.loads(cf.read())
	except:
		pass
	return render_template('control_panel.html', config=config_dict)


@app.route("/set_targets", methods=['POST'])
def targets():
	try:
		config_dict = flask.request.form
		cf = open(config['outdir']+'target_config.json', 'w')
		cf.write(json.dumps(config_dict))
		return "Thank you. Your targeting parameters have been applied."
	except:
		raise
		return "Ruh-roh! Something went wrong..."


def filter_friends(friends):
	# friends should be a list of dicts.
	try:
		cf = open(config['outdir']+'target_config.json', 'r')
		config_dict = json.loads(cf.read())
	except:
		return friends

	def age_match(friend):
		if (not (config_dict['min_age'] and config_dict['max_age'])):
			return True
		elif (config_dict['min_age'] == '0' and config_dict['max_age'] == '120'):
			# If age range is [0,120] then ignore filtering (include people with unknown age)
			return True
		elif (not friend['age']):
			return False
		else:
			return ( friend['age'] >= int(config_dict['min_age']) and friend['age'] <= int(config_dict['max_age']) )

	def gender_match(friend):
		if ((not config_dict['gender']) or config_dict['gender'] == 'both'):
			return True
		elif (not friend['gender']):
			return False
		else:
			return ( config_dict['gender'] == friend['gender'] )

	filtered_friends = [f for f in friends if ( age_match(f) and gender_match(f) )]
	return filtered_friends



############################ UTILS #############################

@app.route('/utils')
def utils():
	return "Combine queue and DB utils (and log reader?)"

@app.route('/queue')
def queueStatus(msg=''):
	if (flask.request.args.get('queueName')):
		qName = flask.request.args.get('queueName')
	else:
		qName = config['queue']
	qSize = StreamReaderQueue.getQueueSize(qName)
	uTs = time.strftime("%Y-%m-%d %H:%M:%S")
	lName = './test_queue.txt'
	return render_template('queue.html', msg=msg, queueName=qName, queueSize=qSize, updateTs=uTs, loadName=lName)

@app.route('/queue_reset')
def queueReset():
	qName = flask.request.args.get('queueName')
	StreamReaderQueue.resetQueue(qName)
	return queueStatus("Queue '%s' has been reset." % (qName))

@app.route('/queue_load')
def queueLoad():
	qName = flask.request.args.get('queueName')
	count = StreamReaderQueue.loadQueueFile(flask.request.args.get('queueName'), flask.request.args.get('loadPath'))
	return queueStatus("Loaded %d entries into queue '%s'." % (count, qName))

@app.route("/db_reset")
def reset():
	ReadStreamDb.dbSetup()
	return "database has been reset"




###########################################################################

if __name__ == "__main__":
	app.run('0.0.0.0', port=5000, debug=False)

