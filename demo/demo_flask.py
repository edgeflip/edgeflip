#!/usr/bin/python
import flask
from flask import Flask, render_template
import ReadStream
import sys



app = Flask(__name__)

@app.route("/", methods=['POST', 'GET'])
def hello():
	guineaPigs = [ { 'id':t[0], 'name':t[1], 'token':t[2] } for t in ReadStream.USER_TUPS ]
	return render_template('demo.html', users=guineaPigs)


@app.route("/fb/", methods=['POST', 'GET'])
def fb():
	return render_template('demo_fb.html')

		
@app.route('/fb/edgeflip', methods=['POST', 'GET'])
def flip_fb():
	return flip_it()

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

if __name__ == "__main__":
#	app.run(debug=True)
	app.run('0.0.0.0', port=5000, debug=False)