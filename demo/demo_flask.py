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

import random # for testing endpoint
import datastructs


app = Flask(__name__)




fbParams = {
				'fb_app_name' : 'edgeflip',
				'fb_app_id' : '471727162864364'
			}

# this should probably end up in a DB...
state_target = { 'EC' : {'state_name' : 'East Calihio', 'name' : 'Smokestax', 'email' : 'smokestax@senate.gov', 'phone' : '(202) 123-4567'} }



@app.route("/", methods=['POST', 'GET'])
def home():
	return render_template('index.html')


@app.route("/ofa_climate/<state>")
def ofa_climate(state):

	state = state.strip().upper()
	targetDict = state_target.get(state)

	if (not targetDict):
		return "Whoopsie! No targets in that state." # you know, or some 404 page...

	objParams = {
					'page_title' : "Tell Sen. %s We're Putting Denial on Trial!" % targetDict['name'],

					'fb_action_type' : 'support',
					'fb_object_type' : 'cause',
					'fb_object_title' : 'Climate Legislation',

					'fb_object_image' : 'http://demo.edgeflip.com/' + flask.url_for('static', filename='doc_brown.jpg'),
					'fb_object_desc' : "The time has come for real climate legislation in America. Tell Senator %s that you stand with President Obama and Organizing for Action on this important issue. We can't wait one more day to act." % targetDict['name'],
					'fb_object_url' : 'http://demo.edgeflip.com/ofa_climate/%s' % state
				}
	objParams.update(fbParams)

	return render_template('ofa_climate_object.html', fbParams=objParams, senInfo=targetDict)

@app.route("/ofa")
@app.route('/all_the_dude_ever_wanted')
@app.route('/demo')
@app.route('/button')
def ofa_auth():
	return render_template('ofa_share_page.html', fbParams=fbParams)


@app.route("/ofa_faces", methods=['POST'])
def ofa_faces():

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
	# zzz No px5 for OFA...
	# stream_queue.loadQueue(config['queue'], [(fbid, tok, "")])

	friendDicts = [ e.toDict() for e in edgesRanked ]

	# Apply control panel targeting filters
	filteredDicts = filter_friends(friendDicts)

	faceFriends = filteredDicts[:6]
	numFace = len(faceFriends)
	allFriends = filteredDicts[:25]

	# zzz state = target state with most friends
	state = 'EC'

	targetDict = state_target.get(state)

	msgParams = {
					'msg1_pre' : "Hi there ",
					'msg1_post' : " -- Contact Sen. %s to say you stand with the president on climate legislation!" % targetDict['name'],
					'msg2_pre' : "Now is the time for real climate legislation, ",
					'msg2_post' : "!",
					'msg_other_prompt' : "Checking friends on the left will add tags for them (type around their names):",
					'msg_other_init' : "Replace this text with your message for " 
				}

	actionParams = 	{
						'fb_action_type' : 'support',
						'fb_object_type' : 'cause',
						'fb_object_url' : 'http://demo.edgeflip.com/ofa_climate/%s' % state
					}
	actionParams.update(fbParams)

	return render_template('ofa_faces_table.html', fbParams=actionParams, msgParams=msgParams, senInfo=targetDict,
							face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace)


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

# Endpoint for testing a faces response...
# (might just want to ultimately do this inline by passing a test mode param so we can actually spin up threads, etc.)
@app.route("/face_test", methods=['GET','POST'])
def face_test():

	# Simulate taking to facebook with a 0-7 second sleep
	s = random.randint(0,7)
	time.sleep(s)

	# Generate between 50 and 450 fake friend edges
	fc = random.randint(50,650)
	edgesUnranked = []
	for i in range(fc):

		muts = random.randint(0,25)
		primPhoto = random.randint(0,10)
		otherPhoto = random.randint(0,20)

		edgesUnranked.append(
			datastructs.Edge(
					datastructs.UserInfo(500876410, 'Rayid', 'Ghani', 'male', datetime.date(1975,03,14), 'Chicago', 'Illinois'),
					datastructs.FriendInfo(500876410, 6963, 'Bob', 'Newhart', 'male', datetime.date(1930,01,01), 'Chicago', 'Illinois', primPhoto, otherPhoto, muts),
					random.randint(0,10), random.randint(0,5), random.randint(0,3), random.randint(0,3), random.randint(0,7), random.randint(0,3), random.randint(0,5),
					random.randint(0,10), random.randint(0,5), random.randint(0,3), random.randint(0,3), random.randint(0,7), random.randint(0,3), random.randint(0,5),
					primPhoto, otherPhoto, muts
				)

			)

#	friendDicts = 	[ 
#						{'id': 123456789, 'fname': 'Bob', 'lname': 'Newhart', 'name': 'Bob Newhart', 
#						 'gender': 'male', 'age': 63, 'city': 'Chicago', 'state': 'Illinois', 'score': 0.43984,
#						 'desc': '0 0 0 0 0 0 0 0 0 0'}
#					]*100


	# Actually rank these edges and generate friend dictionaries from them
	edgesRanked = ranking.getFriendRanking(500876410, edgesUnranked, requireOutgoing=False)
	friendDicts = [ e.toDict() for e in edgesRanked ]

	# Apply control panel targeting filters
	filteredDicts = filter_friends(friendDicts)

	faceFriends = filteredDicts[:6]
	numFace = len(faceFriends)
	allFriends = filteredDicts[:25]

	# zzz state = target state with most friends
	state = 'EC'

	targetDict = state_target.get(state)

	msgParams = {
					'msg1_pre' : "Hi there ",
					'msg1_post' : " -- Contact Sen. %s to say you stand with the president on climate legislation!" % targetDict['name'],
					'msg2_pre' : "Now is the time for real climate legislation, ",
					'msg2_post' : "!",
					'msg_other_prompt' : "Checking friends on the left will add tags for them (type around their names):",
					'msg_other_init' : "Replace this text with your message for " 
				}

	actionParams = 	{
						'fb_action_type' : 'support',
						'fb_object_type' : 'cause',
						'fb_object_url' : 'http://demo.edgeflip.com/ofa_climate/%s' % state
					}
	actionParams.update(fbParams)

	return render_template('ofa_faces_table.html', fbParams=actionParams, msgParams=msgParams, senInfo=targetDict,
							face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace)




###########################################################################

if __name__ == "__main__":
	app.run('0.0.0.0', port=5000, debug=False)

