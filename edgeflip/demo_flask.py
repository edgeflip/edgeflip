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


if __name__ == "__main__":
    app.run('0.0.0.0', port=5000, debug=False)

