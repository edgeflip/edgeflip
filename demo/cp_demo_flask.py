#!/usr/bin/python
import flask
from flask import Flask, render_template
import sys
import json



app = Flask(__name__)

@app.route("/", methods=['POST', 'GET'])
def hello():
	return "Hello World!"


@app.route("/cp", methods=['POST', 'GET'])
@app.route("/control_panel", methods=['POST', 'GET'])
def cp():
	config_dict = {}
	try:
		cf = open('edgeflip/target_config.json', 'r')
		config_dict = json.loads(cf.read())
	except:
		pass
	return render_template('control_panel.html', config=config_dict)


@app.route("/set_targets", methods=['POST'])
def targets():
	try:
		config_dict = flask.request.form
		cf = open('edgeflip/target_config.json', 'w')
		cf.write(json.dumps(config_dict))
		return "Thank you. Your targeting parameters have been applied."
	except:
		raise
		return "Ruh-roh! Something went wrong..."

if __name__ == "__main__":
	app.run(debug=True)
