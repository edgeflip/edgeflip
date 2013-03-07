#!/usr/bin/python
import flask
from flask import Flask, render_template
#import ReadStream
import database
import facebook
import ranking
import stream_queue
import sys
import json
import time
from config import config
import urllib2 # Just for handling errors raised from facebook module. Seems like this should be unncessary...




app = Flask(__name__)




@app.route("/", methods=['POST', 'GET'])
def home():
	return render_template('index.html')

@app.route('/demo')
@app.route('/button')
@app.route('/all_the_dude_ever_wanted')
def button_man():
	return render_template('frame_wide.html')

@app.route('/demo_faces', methods=['POST'])
def face_it():
	sys.stderr.write("flask.request.json: %s\n" % (str(flask.request.json)))

	fbid = int(flask.request.json['fbid'])
	tok = flask.request.json['token']
	num = int(flask.request.json['num'])

	# Try extending the token. If we hit an error, proceed with what we got from the page.
	# zzz Will want to do this with the rank demo when we switch away from Shari!
	try:
		newToken = facebook.extendTokenFb(tok)
		tok = newToken
	except (urllib2.URLError, urllib2.HTTPError, IndexError, KeyError):
		pass # Something went wrong, but the facebook script already logged it, so just go with the original token

	conn = database.getConn()
	user = database.getUserDb(conn, fbid, config['freshness'], freshnessIncludeEdge=True)

	edgesRanked = []
	if (user is not None): # it's fresh
		edgesRanked = ranking.getFriendRankingBestAvailDb(conn, fbid, threshold=0.5)
	else:
		edgesUnranked = facebook.getFriendEdgesFb(fbid, tok, requireOutgoing=False)
		edgesRanked   = ranking.getFriendRanking(fbid, edgesUnranked, requireOutgoing=False)
		# spawn off a separate thread to do the database writing
		user = edgesRanked[0].primary if edgesRanked else facebook.getUserFb(fbid, tok)
		database.updateDb(user, tok, edgesRanked, background=True)
	conn.close()

	# now, spawn a full crawl in the background
	stream_queue.loadQueue(config['queue'], [(fbid, tok, "")])

	friendDicts = [ e.toDict() for e in edgesRanked ]

	# Apply control panel targeting filters
	filteredDicts = filter_friends(friendDicts)

	faceFriends = filteredDicts[:6]
	numFace = len(faceFriends)
	allFriends = filteredDicts[:25]
	ret = render_template('faces_table_wide.html', face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace)

	return ret


@app.route('/rank')
def rank_demo():
	default_users = {
						'shari': { 'fbid': 1509232539, 'tok': 'AAABlUSrYhfIBAFOpiiSrYlBxIvCgQXMhPPZCUJWM70phLO4gQbssC3APFza3kZCMzlgcMZAkmTjZC9UACIctzDD4pn2ulXkZD'},
						'rayid': { 'fbid': 500876410, 'tok': 'AAAGtCIn5MuwBAEaZBhZBr1yK6QfUfhgTZBMKzUt9mkapze1pzXYFZAkvBssMoMar0kQ0WTR6psczIkTiU2KUUdduES8tZCrZBfwFlVh3k71gZDZD'},
						'matt': { 'fbid': 100003222687678, 'tok': 'AAAGtCIn5MuwBAMQ9d0HMAYuHgzSadSNiZAQbGxellczZC1OygQzZBx3vPeStoOhM9j05RmCJhOfcc7OMG4I2pCl2RvdlZCCzAbRNbXic9wZDZD'},
						'6963': { 'fbid': 6963, 'tok': 'AAAGtCIn5MuwBACC6710Xe3HiUK89U9C9eN58uQPGmfVb83HaQ4ihVvCLAmECtJ0Nttyf3ck59paUirvtZBVZC9kZBMrZCT0ZD'}
					}

	rank_user = flask.request.args.get('user', '').lower()
	fbid = default_users.get(rank_user, {}).get('fbid', None)
	tok = default_users.get(rank_user, {}).get('tok', None)
	return render_template('rank_demo.html', fbid=fbid, tok=tok)

@app.route('/rank_faces', methods=['POST'])
def rank_faces():
	import time
	
	fbid = int(flask.request.json['fbid'])
	tok = flask.request.json['token']
	rankfn = flask.request.json['rankfn']

	if (rankfn.lower() == "px4"):

		# first, spawn a full crawl in the background
		stream_queue.loadQueue(config['queue'], [(fbid, tok, "")])

		# now do a partial crawl real-time
		edgesUnranked = facebook.getFriendEdgesFb(fbid, tok, requireOutgoing=False)
		edgesRanked = ranking.getFriendRanking(fbid, edgesUnranked, requireOutgoing=False)
		user = edgesRanked[0].primary if (edgesUnranked) else facebook.getUserFb(fbid, tok) # just in case they have no friends

		# spawn off a separate thread to do the database writing
		database.updateDb(user, tok, edgesRanked, background=True)

	else:
 		edgesRanked = ranking.getFriendRankingDb(None, fbid, requireOutgoing=True)

	friendDicts = [ e.toDict() for e in edgesRanked ]

	# Apply control panel targeting filters
	filteredDicts = filter_friends(friendDicts)

	ret = render_template('rank_faces.html', rankfn=rankfn, face_friends=filteredDicts)
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

	def location_match(friend):
		# NOTE: Right now, control panel just has state-level location filtering!!
		if ( (not config_dict['location']) or config_dict['location'] == 'any'):
			return True
		elif (not friend['state']):
			return False
		else:
			return ( config_dict['location'] == friend['state'] )

	filtered_friends = [f for f in friends if ( age_match(f) and gender_match(f) and location_match(f) )]
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
	qSize = stream_queue.getQueueSize(qName)
	uTs = time.strftime("%Y-%m-%d %H:%M:%S")
	lName = './test_queue.txt'
	return render_template('queue.html', msg=msg, queueName=qName, queueSize=qSize, updateTs=uTs, loadName=lName)

@app.route('/queue_reset')
def queueReset():
	qName = flask.request.args.get('queueName')
	stream_queue.resetQueue(qName)
	return queueStatus("Queue '%s' has been reset." % (qName))

@app.route('/queue_load')
def queueLoad():
	qName = flask.request.args.get('queueName')
	count = stream_queue.loadQueueFile(flask.request.args.get('queueName'), flask.request.args.get('loadPath'))
	return queueStatus("Loaded %d entries into queue '%s'." % (count, qName))

@app.route("/db_reset")
def reset():
	database.db.dbSetup()
	return "database has been reset"




###########################################################################

if __name__ == "__main__":
	app.run('0.0.0.0', port=5000, debug=False)

