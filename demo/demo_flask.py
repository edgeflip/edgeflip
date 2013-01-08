#!/usr/bin/python
import flask
from flask import Flask, render_template
import ReadStream
import sys



app = Flask(__name__)

@app.route("/")
def hello():
	guineaPigs = [ { 'id':t[0], 'name':t[1], 'token':t[2] } for t in ReadStream.USER_TUPS ]
	return render_template('demo.html', users=guineaPigs)

@app.route('/edgeflip', methods=['POST', 'GET'])
def flip_it():
	#sys.stderr.write("flask.request: %s\n" % (str(flask.request)))
	#sys.stderr.write("flask.request.json: %s\n" % (str(flask.request.json)))
	user = flask.request.json['fbid']
	tok = flask.request.json['token']

	friendTups = ReadStream.getFriendRanking(user, tok) # id, name, desc, score
	friendDicts = [ { 'id':t[0], 'name':t[1], 'desc':t[2], 'score':t[3] } for t in friendTups ]

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

#@app.route('/js/<filename>')
#def js_file(filename):
	#f = open('js/%s' % filename)
	#return f.read()

if __name__ == "__main__":
	app.run('0.0.0.0', port=5000, debug=False)
