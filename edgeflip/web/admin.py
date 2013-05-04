"""administrative endpoints

utility code - this should all move to scripts

want big red buttons for control

originally from demo_flask.py
"""
import time
import flask

from .. import stream_queue
from .. import database

from ..settings import config

app = flask.Flask(__name__)

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