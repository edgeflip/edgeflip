#!/usr/bin/python
import sys
import time
import datetime
import random
import flask

import facebook
import ranking
import database
import datastructs
import config as conf
config = conf.getConfig(includeDefaults=True)




app = flask.Flask(__name__)
fbParams = { 'fb_app_name': config['fb_app_name'], 'fb_app_id': config['fb_app_id'] }
state_senInfo = conf.readJson(config['ofa_state_config'])  # 'EC' -> {'state_name':'East Calihio',
															# 			'name':'Smokestax',
															# 			'email':'smokestax@senate.gov',
															# 			'phone' : '(202) 123-4567'}




@app.route("/ofa_faces", methods=['POST'])
def ofa_faces():
	sys.stderr.write("flask.request.json: %s\n" % (str(flask.request.json)))
	fbid = int(flask.request.json['fbid'])
	tok = flask.request.json['token']
	campaign = flask.request.json['campaign']
	numFace = int(flask.request.json['num'])

	campaign_filterTups = conf.readJson(config['ofa_campaign_config'])
	filterTups = campaign_filterTups.get(campaign, [])

	# Try extending the token. If we hit an error, proceed with what we got from the page.
	# zzz Will want to do this with the rank demo when we switch away from Shari!
	tok = facebook.extendTokenFb(tok) or tok

	conn = database.getConn()
	user = database.getUserDb(conn, fbid, config['freshness'], freshnessIncludeEdge=True)

	if (user is not None):  # it's fresh
		edgesRanked = ranking.getFriendRankingBestAvailDb(conn, fbid, threshold=0.5)
	else:
		edgesUnranked = facebook.getFriendEdgesFb(fbid, tok, requireIncoming=False, requireOutgoing=False)
		edgesRanked = ranking.getFriendRanking(fbid, edgesUnranked, requireIncoming=False, requireOutgoing=False)
		# spawn off a separate thread to do the database writing
		user = edgesRanked[0].primary if edgesRanked else facebook.getUserFb(fbid, tok)
		database.updateDb(user, tok, edgesRanked, background=True)
	conn.close()

	bestState = getBestStateFromEdges(edgesRanked, state_senInfo.keys())
	if (bestState is not None):
		filterTups.append(('state', 'eq', bestState))
		edgesFiltered = filterEdgesBySec(edgesRanked, filterTups)

		friendDicts = [ e.toDict() for e in edgesFiltered ]
		faceFriends = friendDicts[:numFace]
		allFriends = friendDicts[:25]

		senInfo = state_senInfo[bestState]

		msgParams = {
		'msg1_pre' : "Hi there ",
		'msg1_post' : " -- Contact Sen. %s to say you stand with the president on climate legislation!" % senInfo['name'],
		'msg2_pre' : "Now is the time for real climate legislation, ",
		'msg2_post' : "!",
		'msg_other_prompt' : "Checking friends on the left will add tags for them (type around their names):",
		'msg_other_init' : "Replace this text with your message for "
		}
		actionParams = 	{
		'fb_action_type' : 'support',
		'fb_object_type' : 'cause',
		'fb_object_url' : 'http://demo.edgeflip.com/ofa_climate/%s' % bestState
		}
		actionParams.update(fbParams)
		return flask.render_template('ofa_faces_table.html', fbParams=actionParams, msgParams=msgParams, senInfo=senInfo,
									 face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace)

	else:
		#zzz need to figure out what we do here
		return flask.render_template('ofa_faces_table_generic.html')

def getBestStateFromEdges(edgesRanked, statePool=None, eligibleProportion=0.5):
	edgesSort = sorted(edgesRanked, key=lambda x: x.score, reverse=True)
	elgCount = int(len(edgesRanked) * eligibleProportion)
	edgesElg = edgesSort[:elgCount]  # only grab the top x% of the pool
	state_count = {}
	for e in edgesElg:
		state_count[e.state] = state_count.get(e.state, 0) + 1
	if (statePool is not None):
		for state in state_count.keys():
			if (state not in statePool):
				del state_count[state]
	bestCount = max(state_count.values())
	bestStates = [ state for state, count in state_count.items if (count == bestCount) ]
	if (len(bestStates) == 1):
		return bestStates[0]
	else:
		# there's a tie for first, so grab the state with the best avg scores
		bestState = None
		bestScoreAvg = 0.0
		for state in bestStates:
			edgesState = [ e for e in edgesElg if (e.state == state) ]
			scoreAvg = sum([ e.score for e in edgesState ])
			if (scoreAvg > bestScoreAvg):
				bestState = state
				bestScoreAvg = scoreAvg
		return bestState

def filterEdgesBySec(edges, filterTups):  # filterTups are (attrName, compTag, attrVal)
	str_func = { "min": lambda x, y: x > y, "max": lambda x, y: x < y, "eq": lambda x, y: x == y }
	edgesGood = edges[:]
	for attrName, compTag, attrVal in filterTups:
		filtFunc = lambda e: hasattr(e, attrName) and str_func[compTag](e.secondary.__getattr__(attrName), attrVal)
		edgesGood = [ e for e in edgesGood if filtFunc(e) ]
	return edgesGood


@app.route("/campaign_save", methods=['POST', 'GET'])
def saveCampaign():
	campFileName = int(flask.request.json['campFileName'])
	campName = flask.request.json['campName']
	configTups = flask.request.json['configTups']
	result = conf.writeJsonDict(campFileName, {campName: configTups}, overwriteFile=False)
	if (result):
		return "Thank you. Your targeting parameters have been applied."
	else:
		return "Ruh-roh! Something went wrong..."


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
		return flask.render_template('new_face.html', id=newid, fname=fname, lname=lname)
	else:
		return ''


# Endpoint for testing a faces response...
# (might just want to ultimately do this inline by passing a test mode param so we can actually spin up threads, etc.)
@app.route("/face_test", methods=['GET','POST'])
def face_test():

	maxTime = int(flask.request.args.get('maxtime', 7))

	# Simulate taking to facebook with a 0-7 second sleep
	s = random.randint(0,maxTime)
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

	campaign_filterTups = conf.readJson(config['ofa_campaign_config'])
	campaign = "test"
	filterTups = campaign_filterTups.get(campaign, [])
	edgesFiltered = filterEdgesBySec(edgesRanked, filterTups)

	friendDicts = [ e.toDict() for e in edgesFiltered ]
	faceFriends = friendDicts[:6]
	numFace = len(faceFriends)
	allFriends = friendDicts[:25]

	# zzz state = target state with most friends
	state = 'EC'

	targetDict = state_senInfo.get(state)

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

	return flask.render_template('ofa_faces_table.html', fbParams=actionParams, msgParams=msgParams, senInfo=targetDict,
								 face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace)

