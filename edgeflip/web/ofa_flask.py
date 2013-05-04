#!/usr/bin/python
"""closer to what end user facing webapp should look like

"""

import sys
import time
import datetime
import random
import hashlib
import logging
import flask

import json
import urllib2  # Just for handling errors raised from facebook module. Seems like this should be unncessary...
import os

from .utils import ajaxResponse, generateSessionId, getIP


from .. import facebook
from .. import ranking
from .. import database
from .. import datastructs
from .. import stream_queue
from .. import filtering

from ..settings import config

logger = logging.getLogger(__name__)


app = flask.Flask(__name__)
fbParams = { 'fb_app_name': config['fb_app_name'], 'fb_app_id': config['fb_app_id'] }

# Serves just a button, to be displayed in an iframe
@app.route("/button_man")
def button_man():
    """serves the button in iframe on client site"""
    return flask.render_template('button_man.html', fbParams=fbParams, goto=config.web.button_redirect)

# Serves the actual faces & share message
@app.route("/frame_faces")
def frame_faces():
    """html container (iframe) for client site """
    return flask.render_template('frame_faces.html', fbParams=fbParams)


@app.route("/faces", methods=['POST'])
def faces():
    """return list of faces - HTML snippet"""
    logger.debug("flask.request.json: %s", str(flask.request.json))
    fbid = int(flask.request.json['fbid'])
    tok = flask.request.json['token']
    campaign = flask.request.json.get('campaign')
    numFace = int(flask.request.json['num'])
    sessionId = flask.request.json['sessionid']
    ip = getIP(req = flask.request)

    campaign_filterTups = config.ofa_campaigns
    filterTups = campaign_filterTups.get(campaign, [])

    # Try extending the token. If we hit an error, proceed with what we got from the page.
    #zzz Will want to do this with the rank demo when we switch away from Shari!
    tok = facebook.extendTokenFb(tok) or tok

    """next 60 lines or so get pulled out"""
    conn = database.getConn()
    user = database.getUserDb(conn, fbid, config['freshness'], freshnessIncludeEdge=True)

    if (user is not None):  # it's fresh

        logger.debug("user %s is fresh, getting data from db", fbid)
        edgesRanked = ranking.getFriendRankingBestAvailDb(conn, fbid, threshold=0.5)
    else:
        logger.debug("user %s is not fresh, retrieving data from fb", fbid)
        edgesUnranked = facebook.getFriendEdgesFb(fbid, tok, requireIncoming=False, requireOutgoing=False)
        edgesRanked = ranking.getFriendRanking(fbid, edgesUnranked, requireIncoming=False, requireOutgoing=False)
        user = edgesRanked[0].primary if edgesRanked else facebook.getUserFb(fbid, tok)
        database.updateDb(user, tok, edgesRanked, background=True)     # zzz should spawn off thread to do db writing
    conn.close()

    bestState = filtering.getBestSecStateFromEdges(edgesRanked, config.ofa_states.keys(), eligibleProportion=1.0)
    if (bestState is not None):
        filterTups.append(('state', 'eq', bestState))
        edgesFiltered = filtering.filterEdgesBySec(edgesRanked, filterTups)
        logger.debug("have %d edges after filtering on %s", len(edgesFiltered), str(filterTups))

        friendDicts = [ e.toDict() for e in edgesFiltered ]
        faceFriends = friendDicts[:numFace]
        allFriends = friendDicts[:25]

        senInfo = config.ofa_states[bestState]

        """these messages move into database"""
        msgParams = {
        'msg1_pre' : "Hi there ",
        'msg1_post' : " -- Contact Sen. %s to say you stand with the president on climate legislation!" % senInfo['name'],
        'msg2_pre' : "Now is the time for real climate legislation, ",
        'msg2_post' : "!",
        'msg_other_prompt' : "Checking friends on the left will add tags for them (type around their names):",
        'msg_other_init' : "Replace this text with your message for "
        }
        actionParams =     {
        'fb_action_type' : 'support',
        'fb_object_type' : 'cause',
        'fb_object_url' : flask.url_for('fb_object', state=bestState, _external=True)
        }
        actionParams.update(fbParams)
        logger.debug('fb_object_url: ' + actionParams['fb_object_url'])

        content = actionParams['fb_app_name']+':'+actionParams['fb_object_type']+' '+actionParams['fb_object_url']
        if (not sessionId):
            sessionId = generateSessionId(ip, content)

        database.writeEventsDb(sessionId, ip, fbid, [f['id'] for f in faceFriends], 'shown', actionParams['fb_app_id'], content, None, background=True)
        return ajaxResponse(flask.render_template('faces_table.html', fbParams=actionParams, msgParams=msgParams, senInfo=senInfo,
                                     face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace), 200, sessionId)

    else:
        content = 'edgeflip:cause http://allyourfriendsarestateless.com/'
        if (not sessionId):
            sessionId = generateSessionId(ip, content)
        return ajaxResponse('all of your friends are stateless', 200, sessionId)

@app.route("/fb_object")
def fb_object():
    """endpoint linked to on facebook.com

    redirect to client page in JS (b/c this must live on our domain for facebook to crawl)
    """
    state = flask.request.args.get('state')
    if state is None:
        return "No state specified", 404
    
    senInfo = config.ofa_states.get(state)
    if (not senInfo):
        return "Whoopsie! No targets in that state.", 404  # you know, or some 404 page...

    objParams = {
    'page_title': "Tell Sen. %s We're Putting Denial on Trial!" % senInfo['name'],
    'fb_action_type': 'support',
    'fb_object_type': 'cause',
    'fb_object_title': 'Climate Legislation',
    'fb_object_image': 'http://demo.edgeflip.com/' + flask.url_for('static', filename='doc_brown.jpg'),
    'fb_object_desc': "The time has come for real climate legislation in America. Tell Senator %s that you stand with President Obama and Organizing for Action on this important issue. We can't wait one more day to act." % senInfo['name'],
    'fb_object_url' : flask.url_for('fb_object', state=state, _external=True)
    }
    objParams.update(fbParams)

    # zzz Are we going to want/need to pass URL parameters to this redirect?
    redirectURL = config.web.fb_object_redirect

    return flask.render_template('fb_object.html', fbParams=objParams, redirectURL=redirectURL)


@app.route('/suppress', methods=['POST'])
def suppress():
    """called when user declines a friend. returns a new friend (HTML snippet)

    """
    userid = flask.request.json['userid']
    appid = flask.request.json['appid']
    content = flask.request.json['content']
    oldid = flask.request.json['oldid']
    sessionId = flask.request.json['sessionid']
    ip = getIP(req = flask.request)

    newid = flask.request.json['newid']
    fname = flask.request.json['fname']
    lname = flask.request.json['lname']

    if (not sessionId):
        sessionId = generateSessionId(ip, content)

    database.writeEventsDb(sessionId, ip, userid, [oldid], 'suppressed', appid, content, None, background=True)

    if (newid != ''):
        database.writeEventsDb(sessionId, ip, userid, [newid], 'shown', appid, content, None, background=True)
        return ajaxResponse(flask.render_template('new_face.html', id=newid, fname=fname, lname=lname), 200, sessionId)
    else:
        return ajaxResponse('', 200, sessionId)

@app.route('/record_event', methods=['POST'])
def recordEvent():
    """endpoint that stores client events (clicks, etc.) for analytics

    used on events that don't generate any useful data themselves
    """
    userId = flask.request.json.get('userid')
    userId = userId or None
    appId = flask.request.json['appid']
    content = flask.request.json['content']
    actionId = flask.request.json.get('actionid')
    friends = [ int(f) for f in flask.request.json.get('friends', []) ]
    friends = friends or [None]
    eventType = flask.request.json['eventType']
    sessionId = flask.request.json['sessionid']
    ip = getIP(req = flask.request)

    if (eventType not in ['button_load', 'button_click', 'authorized', 'auth_fail', 'shared', 'clickback']):
        return "Ah, ah, ah. You didn't say the magic word.", 403

    if (not sessionId):
        sessionId = generateSessionId(ip, content)

    database.writeEventsDb(sessionId, ip, userId, friends, eventType, appId, content, actionId, background=True)
    return ajaxResponse('', 200, sessionId)


@app.route("/health_check")
@app.route("/hes_a_good_man_and_thorough")
def say_ahhh():
    """ break up into newrelic, internal monitoring

    need aliveness check for ELB.

    """
    iselb = flask.request.args.get('elb', '').lower()
    if (iselb == 'true'): return "It's Alive!", 200

    isdevops = flask.request.args.get('devops', '').lower()
    if (isdevops != 'true'): return "Sorry... you can't access this page", 403

    try:
        # Make sure we can connect and return results from DB
        conn = database.getConn()
        curs = conn.cursor()
        curs.execute("SELECT 1+1")
        assert curs.fetchone()[0] == 2
        conn.close()

        # Make sure we can talk to FB and get simple user info back
        fbresp = facebook.getUrlFb("http://graph.facebook.com/6963")
        assert int(fbresp['id']) == 6963

        # zzz Do we want to check system-level things here, too??

        return "Fit As A Fiddle!", 200
    except:
        # zzz One day, provide more detailed output...
        return "Ruh-Roh - Health Check Failed!", 500