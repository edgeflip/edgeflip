import flask
from flask import Flask
import FacebookFriends as fbf

app = Flask(__name__)

@app.route("/")
def hello():
#	friends = ''
#	try:
#		user = fbf.FbUser(500876410, 'rayid', 'AAABlUSrYhfIBAH7jkzeLZAos8m8aET3rfZBmycGvHLrUEroS3XghNzATCuOwsbQ8JK5lgjDRMHAvasMxgIWWYbOSh5G2awxbep3PMONgZDZD')
#		friends = str(user.getFriends())
#	except:
#		friends = 'Doh'
#	return friends
#	return "Hello World!"
#	x = ''
#	try:
#		x = str(flask.url_for('static', filename='js/jquery.js'))
#	except e:
#		x = str(e)
	f = open('hi.html', 'r')
	return f.read()

@app.route('/edgeflip', methods=['POST'])
def flip_it():
	fb_id = flask.request.json['fb_id']
	name = flask.request.json['name']
	fb_token = flask.request.json['fb_token']
#	flipper = 'Flip my edge %s' % '12345'
#	return flask.jsonify(resp = flipper)
	friends = ''
	try:
		user = fbf.FbUser(fb_id, name, fb_token)
		friends = '<H2>Your Friends Are...</H2>' + str(user.getFriends())
	except:
		friends = 'Doh'
	return flask.jsonify(resp = friends)

@app.route('/js/<filename>')
def js_file(filename):
	f = open('js/%s' % filename)
	return f.read()

if __name__ == "__main__":
    app.run()
