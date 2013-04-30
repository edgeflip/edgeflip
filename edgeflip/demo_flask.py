#!/usr/bin/python
"""bastard child we pretend doesn't exist

"""

import flask


from . import database
from . import facebook
from . import ranking
from . import stream_queue

import sys
import json
import time
import urllib2  # Just for handling errors raised from facebook module. Seems like this should be unncessary...
import logging
import os

from .settings import config 

from . import datastructs

import datetime


app = flask.Flask(__name__)

@app.route("/", methods=['POST', 'GET'])
def home():
    return flask.render_template('index.html')


############################ UTILS #############################
"""utility code - this should all move to scripts

want big red buttons for control

"""


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
    return flask.render_template('queue.html', msg=msg, queueName=qName, queueSize=qSize, updateTs=uTs, loadName=lName)

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

