#!/usr/bin/python
import flask
from flask import Flask, render_template
import ReadStream
import ReadStreamDb
import sys
import json

from Config import config
# try:
# 	ef_config = open('edgeflip.config', 'r')
# 	ef_dict = json.loads(ef_config.read())
# 	if (not ef_dict['outdir']):
# 		ef_dict['outdir'] = ''
# except:
# 	ef_dict = {'outdir' : ''}


app = Flask(__name__)


@app.route("/reset")
def reset():
	ReadStreamDb.dbSetup()
	return "database has been reset"

@app.route("/", methods=['POST', 'GET'])
def hello():
	guineaPigs = [ { 'id':t[0], 'name':t[1], 'token':t[2] } for t in ReadStream.USER_TUPS ]
	return render_template('demo.html', users=guineaPigs)


@app.route("/fb/", methods=['POST', 'GET'])
def fb():
	return render_template('demo_fb.html')

		
@app.route('/crawl', methods=['POST'])
def read_stream():
	userId = flask.request.json['fbid']
	tok = flask.request.json['token']
	includeOutgoing = flask.request.json['outgoing']



	return flip_it()


@app.route('/fb/edgeflip', methods=['POST', 'GET'])
@app.route('/edgeflip', methods=['POST', 'GET'])
def flip_it():
	#sys.stderr.write("flask.request: %s\n" % (str(flask.request)))
	sys.stderr.write("flask.request.json: %s\n" % (str(flask.request.json)))
	fbid = flask.request.json['fbid']
	tok = flask.request.json['token']
	num = int(flask.request.json['num'])

	conn = ReadStreamDb.getConn()
	user = ReadStream.getUserFb(fbid, tok)
	ReadStream.updateUserDb(conn, user, tok, None)

 	# first, do a partial crawl for new friends
	newCount = ReadStream.updateFriendEdgesDb(conn, fbid, tok, readFriendStream=False, overwrite=False)

	# now, spawn a full crawl in the background
##	pid = ReadStream.spawnCrawl(fbid, tok, includeOutgoing=True, overwrite=False)
	#friendTups = ReadStream.getFriendRankingCrawl(conn, fbid, tok, includeOutgoing=False)
	friendTups = ReadStream.getFriendRanking(conn, fbid, includeOutgoing=False)

	#friendDicts = [ { 'rank':i, 'id':t[0], 'name':t[1], 'desc':t[2], 'score':"%.4f"%t[3] } for i, t in enumerate(friendTups) ]
	friendDicts = []
	for i, t in enumerate(friendTups):
		fd = { 'rank':i, 'id':t[0], 'name':" ".join(t[1:3]), 'gender':t[3], 'age':t[4],  'desc':t[5], 'score':"%.4f"%float(t[6]) }
		for c, count in enumerate(t[2].split()):
			fd['count' + str(c)] = count
		friendDicts.append(fd)

	for fd in friendDicts:
		sys.stderr.write(str(fd) + "\n")

	# Apply control panel targeting filters
	filteredDicts = filter_friends(friendDicts)

	ret = render_template('friend_table.html', friends=filteredDicts)
	#sys.stderr.write("rendered: " + str(ret) + "\n")
	return ret
		

@app.route('/edgeflip_faces', methods=['POST'])
def face_it():
	sys.stderr.write("flask.request.json: %s\n" % (str(flask.request.json)))
	fbid = flask.request.json['fbid']
	tok = flask.request.json['token']
	num = int(flask.request.json['num'])

	conn = ReadStreamDb.getConn()
	user = ReadStream.getUserFb(fbid, tok)
	ReadStream.updateUserDb(conn, user, tok, None)

 	# first, do a partial crawl for new friends
	newCount = ReadStream.updateFriendEdgesDb(conn, fbid, tok, readFriendStream=False, overwrite=False)

	# now, spawn a full crawl in the background
##	pid = ReadStream.spawnCrawl(fbid, tok, includeOutgoing=True, overwrite=False)
	#friendTups = ReadStream.getFriendRankingCrawl(conn, fbid, tok, includeOutgoing=False)
	#friendTups = ReadStream.getFriendRanking(conn, fbid, includeOutgoing=False)
	friendTups = ReadStream.getFriendRankingBestAvail(conn, fbid, threshold=0.5)

	#friendDicts = [ { 'rank':i, 'id':t[0], 'name':t[1], 'desc':t[2], 'score':"%.4f"%t[3] } for i, t in enumerate(friendTups) ]
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
#	shareurl = 'http://www.foulballtracker.com/'
	allFriends = filteredDicts[:25]
	ret = render_template('faces_table_wide.html', face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace)

	return ret

@app.route('/button')
@app.route('/all_the_dude_ever_wanted')
def button_man():
	return render_template('frame_wide.html')

@app.route('/rank_demo')
def rank_demo():
	return render_template('rank_demo.html')

@app.route('/edgeflip_rankPeople', methods=['POST'])
def rank_people():
	import time
	#print "Hello there!"
	
	# fbid: fbid,
	# token: accessToken,
	# num: num,
	# rankfn: 'px4'
	fbid = flask.request.json['fbid']
	tok = flask.request.json['token']
	rankfn = flask.request.json['rankfn']

	conn = ReadStreamDb.getConn()
	user = ReadStream.getUserFb(fbid, tok)
	ReadStream.updateUserDb(conn, user, tok, None)

 	# first, do a partial crawl for new friends
	newCount = ReadStream.updateFriendEdgesDb(conn, fbid, tok, readFriendStream=False, overwrite=False)

	if (rankfn.lower() == "px4"):
		# now, spawn a full crawl in the background
		pid = ReadStream.spawnCrawl(fbid, tok, includeOutgoing=True, overwrite=False)
		#friendTups = ReadStream.getFriendRankingCrawl(conn, fbid, tok, includeOutgoing=False)
 		friendTups = ReadStream.getFriendRanking(conn, fbid, includeOutgoing=False)
	else:
 		friendTups = ReadStream.getFriendRanking(conn, fbid, includeOutgoing=True)

	friendDicts = []
	for i, t in enumerate(friendTups):
		# friend.id, friend.fname, friend.lname, friend.gender, friend.age, desc, score
		fd = { 'rank':i, 'id':t[0], 'name':" ".join(t[1:3]), 'gender':t[3], 'age':t[4],  'desc':t[5].replace('None', '&Oslash;'), 'score':"%.4f"%float(t[6]) }
		friendDicts.append(fd)

	# Apply control panel targeting filters
	filteredDicts = filter_friends(friendDicts)

	ret = render_template('rank_faces.html', face_friends=filteredDicts)
	return ret



@app.route('/mention')
def mention_test():
	return render_template('friend_picker.html')

@app.route('/pretty_faces')
def pretty_face():
	return render_template('pretty_face.html')

@app.route('/wide_faces')
def wide_face():
	return render_template('wide_face.html')	

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



###########################################################################

if __name__ == "__main__":
	app.run('0.0.0.0', port=5000, debug=False)

