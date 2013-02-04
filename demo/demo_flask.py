#!/usr/bin/python
import flask
from flask import Flask, render_template
import ReadStream
import ReadStreamDb
import sys



app = Flask(__name__)

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
	user = flask.request.json['fbid']
	tok = flask.request.json['token']
	num = int(flask.request.json['num'])

	friendTups = ReadStream.getFriendRanking(user, tok, num) # id, name, desc, score
	#friendDicts = [ { 'rank':i, 'id':t[0], 'name':t[1], 'desc':t[2], 'score':"%.4f"%t[3] } for i, t in enumerate(friendTups) ]
	friendDicts = []
	for i, t in enumerate(friendTups):
		fd = { 'rank':i, 'id':t[0], 'name':t[1], 'desc':t[2], 'score':"%.4f"%t[3] }
		for c, count in enumerate(t[2].split()):
			fd['count' + str(c)] = count
		friendDicts.append(fd)

	for fd in friendDicts:
		sys.stderr.write(str(fd) + "\n")

	ret = render_template('friend_table.html', friends=friendDicts)
	#sys.stderr.write("rendered: " + str(ret) + "\n")
	return ret
		
	#return flask.jsonify(resp=friendTups)

	#try:
		#friendTups = ReadStream.getFriendRanking(user, tok) # id, name, desc, score
		#friendHtml = "<table>"
		#for i, (fid, name, desc, score) in enumerate(friendTups):
			#friendHtml += "<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (i, fid, name, desc, score)
		#friendHtml += "</table>"	
	#except:
		#friendHtml = 'Doh'

@app.route('/edgeflip_faces', methods=['POST'])
def face_it():
	sys.stderr.write("flask.request.json: %s\n" % (str(flask.request.json)))
	user = flask.request.json['fbid']
	tok = flask.request.json['token']
	num = int(flask.request.json['num'])

	friendTups = ReadStream.getFriendRanking(user, tok, num) # id, name, desc, score
	#friendDicts = [ { 'rank':i, 'id':t[0], 'name':t[1], 'desc':t[2], 'score':"%.4f"%t[3] } for i, t in enumerate(friendTups) ]
	friendDicts = []
	for i, t in enumerate(friendTups):
		fd = { 'rank':i, 'id':t[0], 'name':t[1], 'desc':t[2], 'score':"%.4f"%t[3] }
		for c, count in enumerate(t[2].split()):
			fd['count' + str(c)] = count
		friendDicts.append(fd)

	for fd in friendDicts:
		sys.stderr.write(str(fd) + "\n")

	faceFriends = friendDicts[:6]
	numFace = len(faceFriends)
	shareurl = 'http://www.foulballtracker.com/'
	ret = render_template('faces_table.html', face_friends=faceFriends, numFriends=numFace, url = shareurl)

	return ret

@app.route('/button')
@app.route('/all_the_dude_ever_wanted')
def button_man():
	return render_template('frame.html')

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
		friendDicts = []
		for i, t in enumerate(friendTups):
			# friend.id, friend.fname, friend.lname, friend.gender, friend.age, score
			fd = { 'rank':i, 'id':t[0], 'name':" ".join(t[1:3]), 'gender':t[3], 'age':t[4], 'score':"%.4f"%float(t[5]) }
			friendDicts.append(fd)
		ret = render_template('rank_faces.html', face_friends=friendDicts)
		return ret

	else:
 		friendTups = ReadStream.getFriendRanking(conn, fbid, includeOutgoing=True)
		friendDicts = []
		for i, t in enumerate(friendTups):
			# friend.id, friend.fname, friend.lname, friend.gender, friend.age, score
			fd = { 'rank':i, 'id':t[0], 'name':" ".join(t[1:3]), 'gender':t[3], 'age':t[4], 'score':"%.4f"%float(t[5]) }
			friendDicts.append(fd)
		ret = render_template('rank_faces.html', face_friends=friendDicts)
		return ret





@app.route('/mention')
def mention_test():
	return render_template('friend_picker.html')

if __name__ == "__main__":
#	app.run(debug=True)
	app.run('0.0.0.0', port=5000, debug=False)
