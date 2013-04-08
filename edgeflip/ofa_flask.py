#!/usr/bin/python
import sys
import time
import datetime
import random
import hashlib
import logging
import flask

from . import facebook
from . import ranking
from . import database
from . import datastructs
from . import config as conf
config = conf.getConfig(includeDefaults=True)




app = flask.Flask(__name__)
fbParams = { 'fb_app_name': config['fb_app_name'], 'fb_app_id': config['fb_app_id'] }
state_senInfo = conf.readJson(config['ofa_state_config'])  # 'East Calihio' -> {'state_name':'East Calihio',
                                                            #             'name':'Smokestax',
                                                            #             'email':'smokestax@senate.gov',
                                                            #             'phone' : '(202) 123-4567'}


# This is an example endpoint... in reality, this page would be on OFA servers
@app.route("/ofa")
def ofa_auth():
    return flask.render_template('ofa_share_wrapper.html')

# This is an example endpoint... in reality, this page would be on OFA servers
@app.route("/ofa_share")
def ofa_share():
    return flask.render_template('ofa_faces_wrapper.html')


# Serves just a button, to be displayed in an iframe
@app.route("/button_man")
def button_man():
    return flask.render_template('cicci.html', fbParams=fbParams, goto=config['ofa_button_redirect'])

# Serves the actual faces & share message
@app.route("/frame_faces")
def frame_faces():
    return flask.render_template('ofa_frame_faces.html', fbParams=fbParams)


@app.route("/ofa_faces", methods=['POST'])
def ofa_faces():
    sys.stderr.write("flask.request.json: %s\n" % (str(flask.request.json)))
    fbid = int(flask.request.json['fbid'])
    tok = flask.request.json['token']
    campaign = flask.request.json.get('campaign')
    numFace = int(flask.request.json['num'])
    sessionId = flask.request.json['sessionid']
    ip = getIP(req = flask.request)

    campaign_filterTups = conf.readJson(config['ofa_campaign_config'])
    filterTups = campaign_filterTups.get(campaign, [])

    # Try extending the token. If we hit an error, proceed with what we got from the page.
    #zzz Will want to do this with the rank demo when we switch away from Shari!
    tok = facebook.extendTokenFb(tok) or tok

    conn = database.getConn()
    user = database.getUserDb(conn, fbid, config['freshness'], freshnessIncludeEdge=True)

    if (user is not None):  # it's fresh
#    if (False): # Disable DB entirely for now because it's faster to crawl px3...
        logging.debug("user %s is fresh, getting data from db" % fbid)
        edgesRanked = ranking.getFriendRankingBestAvailDb(conn, fbid, threshold=0.5)
    else:
        logging.debug("user %s is not fresh, retrieving data from fb" % fbid)
        edgesUnranked = facebook.getFriendEdgesFb(fbid, tok, requireIncoming=False, requireOutgoing=False)
        edgesRanked = ranking.getFriendRanking(fbid, edgesUnranked, requireIncoming=False, requireOutgoing=False)
        user = edgesRanked[0].primary if edgesRanked else facebook.getUserFb(fbid, tok)
        database.updateDb(user, tok, edgesRanked, background=True)     # zzz should spawn off thread to do db writing
    conn.close()

    bestState = getBestSecStateFromEdges(edgesRanked, state_senInfo.keys(), eligibleProportion=1.0)
    if (bestState is not None):
        filterTups.append(('state', 'eq', bestState))
        edgesFiltered = filterEdgesBySec(edgesRanked, filterTups)
        logging.debug("have %d edges after filtering on %s" % (len(edgesFiltered), str(filterTups)))

        friendDicts = [ e.toDict() for e in edgesFiltered ]
        faceFriends = friendDicts[:numFace]
        allFriends = friendDicts[:25]

        senInfo = state_senInfo[bestState]

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
        'fb_object_url' : flask.url_for('ofa_climate', state=bestState, _external=True)  #'http://demo.edgeflip.com/ofa_climate/%s' % bestState
        }
        actionParams.update(fbParams)
        logging.debug('fb_object_url: ' + actionParams['fb_object_url'])

        content = actionParams['fb_app_name']+':'+actionParams['fb_object_type']+' '+actionParams['fb_object_url']
        if (not sessionId):
            sessionId = generateSessionId(ip, content)

        database.writeEventsDb(sessionId, ip, fbid, [f['id'] for f in faceFriends], 'shown', actionParams['fb_app_id'], content, None, background=True)
        return ajaxResponse(flask.render_template('ofa_faces_table.html', fbParams=actionParams, msgParams=msgParams, senInfo=senInfo,
                                     face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace), 200, sessionId)

    else:
        #zzz need to figure out what we do here
        #return flask.render_template('ofa_faces_table_generic.html')
        #database.writeEventsDb(sessionId, ip, fbid, [f['id'] for f in faceFriends], 'shown', actionParams['fb_app_id'],
        #      actionParams['fb_app_name']+':'+actionParams['fb_object_type']+' '+actionParams['fb_object_url'], None, background=True)
        content = 'edgeflip:cause http://allyourfriendsarestateless.com/'
        if (not sessionId):
            sessionId = generateSessionId(ip, content)
        return ajaxResponse('all of your friends are stateless', 200, sessionId)


def getBestSecStateFromEdges(edgesRanked, statePool=None, eligibleProportion=0.5):
    edgesSort = sorted(edgesRanked, key=lambda x: x.score, reverse=True)
    elgCount = int(len(edgesRanked) * eligibleProportion)
    edgesElg = edgesSort[:elgCount]  # only grab the top x% of the pool
    state_count = {}
    for e in edgesElg:
        state_count[e.secondary.state] = state_count.get(e.secondary.state, 0) + 1
    if (statePool is not None):
        for state in state_count.keys():
            if (state not in statePool):
                del state_count[state]
    if (state_count):
        logging.debug("best state counts: %s" % str(state_count))
        bestCount = max(state_count.values() + [0])  # in case we don't get any states
        bestStates = [ state for state, count in state_count.items() if (count == bestCount) ]
        if (len(bestStates) == 1):
            logging.debug("best state returning %s" % bestStates[0])
            return bestStates[0]
        else:
            # there's a tie for first, so grab the state with the best avg scores
            bestState = None
            bestScoreAvg = 0.0
            for state in bestStates:
                edgesState = [ e for e in edgesElg if (e.state == state) ]
                scoreAvg = sum([ e.score for e in edgesState ])
                if (scoreAvg > bestScoreAvg):
                    bestState = state
                    bestScoreAvg = scoreAvg
            logging.debug("best state returning %s" % bestState)
            return bestState
    else:
        return None

def filterEdgesBySec(edges, filterTups):  # filterTups are (attrName, compTag, attrVal)
    str_func = { "min": lambda x, y: x > y, "max": lambda x, y: x < y, "eq": lambda x, y: x == y }
    edgesGood = edges[:]
    for attrName, compTag, attrVal in filterTups:
        logging.debug("filtering %d edges on '%s %s %s'" % (len(edgesGood), attrName, compTag, attrVal))
        filtFunc = lambda e: hasattr(e.secondary, attrName) and str_func[compTag](e.secondary.__dict__[attrName], attrVal)
        edgesGood = [ e for e in edgesGood if filtFunc(e) ]
        logging.debug("have %d edges left" % (len(edgesGood)))
    return edgesGood


@app.route("/ofa_climate/<state>")
def ofa_climate(state):
    #state = state.strip().upper()
    senInfo = state_senInfo.get(state)
    if (not senInfo):
        return "Whoopsie! No targets in that state.", 404  # you know, or some 404 page...

    objParams = {
    'page_title': "Tell Sen. %s We're Putting Denial on Trial!" % senInfo['name'],
    'fb_action_type': 'support',
    'fb_object_type': 'cause',
    'fb_object_title': 'Climate Legislation',
    'fb_object_image': 'http://demo.edgeflip.com/' + flask.url_for('static', filename='doc_brown.jpg'),
    'fb_object_desc': "The time has come for real climate legislation in America. Tell Senator %s that you stand with President Obama and Organizing for Action on this important issue. We can't wait one more day to act." % senInfo['name'],
    'fb_object_url' : flask.url_for('ofa_climate', state=state, _external=True)  #'http://demo.edgeflip.com/ofa_climate/%s' % bestState
    }
    objParams.update(fbParams)

    # zzz Are we going to want/need to pass URL parameters to this redirect?
    redirectURL = flask.url_for('ofa_landing', state=state, _external=True)    # Will actually be client's external URL...

    return flask.render_template('ofa_climate_object.html', fbParams=objParams, redirectURL=redirectURL)


# This is an example endpoint... in reality, this page would be on OFA servers
@app.route("/ofa_landing/<state>")
def ofa_landing(state):
    senInfo = state_senInfo.get(state)
    if (not senInfo):
        return "Whoopsie! No targets in that state.", 404  # you know, or some 404 page...
    pageTitle = "Tell Sen. %s We're Putting Denial on Trial!" % senInfo['name']

    return flask.render_template('ofa_climate_landing.html', senInfo=senInfo, page_title=pageTitle)


@app.route("/campaign_save", methods=['POST', 'GET'])
def saveCampaign():
    campFileName = int(flask.request.json['campFileName'])
    campName = flask.request.json['campName']
    configTups = flask.request.json['configTups']
    result = conf.writeJsonDict(campFileName, {campName: configTups}, overwriteFile=False)
    if (result):
        return "Thank you. Your targeting parameters have been applied."
    else:
        return "Ruh-roh! Something went wrong..."


@app.route('/suppress', methods=['POST'])
def suppress():
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


# @app.route('/clickback', methods=['POST'])
# def clickback():
#     actionid = flask.request.json['actionid']
#     appid = flask.request.json['appid']
#     content = flask.request.json['content']
#     sessionId = flask.request.json['sessionid']
#     ip = getIP(req = flask.request)

#     if (not sessionId):
#         sessionId = generateSessionId(ip, content)

#     database.writeEventsDb(sessionId, ip, None, [None], 'clickback', appid, content, actionid, background=True)
#     resp = flask.make_response('', 200)
#     resp.headers['X-EF-SessionID'] = sessionId
#     return resp

# @app.route('/share', methods=['POST'])
# def recordShare():
#     userid = flask.request.json['userid']
#     actionid = flask.request.json['actionid']
#     appid = flask.request.json['appid']
#     content = flask.request.json['content']
#     friends = [ int(f) for f in flask.request.json['friends'] ]
#     sessionId = flask.request.json['sessionid']
#     ip = getIP(req = flask.request)

#     if (not sessionId):
#         sessionId = generateSessionId(ip, content)

#     database.writeEventsDb(sessionId, ip, userid, friends, 'shared', appid, content, actionid, background=True)
#     resp = flask.make_response('', 200)
#     resp.headers['X-EF-SessionID'] = sessionId
#     return resp

# @app.route('/button_event', methods=['POST'])
# def buttonEvent():
#     userId = flask.request.json['userid']
#     userId = userId or None
#     appId = flask.request.json['appid']
#     content = flask.request.json['content']
#     eventType = flask.request.json['eventType']
#     sessionId = flask.request.json['sessionid']
#     ip = getIP(req = flask.request)

#     if (eventType not in ['button_load', 'button_click', 'authorized', 'auth_fail']):
#         return "Ah, ah, ah. You didn't say the magic word.", 403

#     if (not sessionId):
#         sessionId = generateSessionId(ip, content)

#     database.writeEventsDb(sessionId, ip, userId, [None], eventType, appId, content, None, background=True)
#     resp = flask.make_response('', 200)
#     resp.headers['X-EF-SessionID'] = sessionId
#     return resp

@app.route('/record_event', methods=['POST'])
def recordEvent():
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

    if (eventType not in ['button_load', 'button_click', 'authorized', 'auth_fail', 'share', 'clickback']):
        return "Ah, ah, ah. You didn't say the magic word.", 403

    if (not sessionId):
        sessionId = generateSessionId(ip, content)

    database.writeEventsDb(sessionId, ip, userId, friends, eventType, appId, content, actionId, background=True)
    return ajaxResponse('', 200, sessionId)


def ajaxResponse(content, code, sessionId):
    resp = flask.make_response(content, code)
    resp.headers['X-EF-SessionID'] = sessionId
    return resp

def getIP(req):
    if not req.headers.getlist("X-Forwarded-For"):
       return req.remote_addr
    else:
       return req.headers.getlist("X-Forwarded-For")[0]

def generateSessionId(ip, content, timestr=None):
    if (not timestr):
        timestr = '%.10f' % time.time()
    # Is MD5 the right strategy here?
    sessionId = hashlib.md5(ip+content+timestr).hexdigest()
    logging.debug('Generated session id %s for IP %s with content %s at time %s' % (sessionId, ip, content, timestr))
    return sessionId


@app.route("/health_check")
@app.route("/hes_a_good_man_and_thorough")
def say_ahhh():

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

# Endpoint for testing a faces response...
# (might just want to ultimately do this inline by passing a test mode param so we can actually spin up threads, etc.)
@app.route("/face_test", methods=['GET','POST'])
def face_test():

    maxTime = int(flask.request.args.get('maxtime', 7))

    # Simulate taking to facebook with a 0-7 second sleep
    s = random.randint(0,maxTime)
    time.sleep(s)

    # Generate between 50 and 450 fake friend edges
    fc = random.randint(50,650)
    edgesUnranked = []
    for i in range(fc):

        muts = random.randint(0,25)
        primPhoto = random.randint(0,10)
        otherPhoto = random.randint(0,20)

        edgesUnranked.append(
            datastructs.Edge(
                datastructs.UserInfo(500876410, 'Rayid', 'Ghani', 'male', datetime.date(1975,03,14), 'Chicago', 'Illinois'),
                datastructs.FriendInfo(500876410, 6963, 'Bob', 'Newhart', 'male', datetime.date(1930,01,01), 'Chicago', 'Illinois', primPhoto, otherPhoto, muts),
                random.randint(0,10), random.randint(0,5), random.randint(0,3), random.randint(0,3), random.randint(0,7), random.randint(0,3), random.randint(0,5),
                random.randint(0,10), random.randint(0,5), random.randint(0,3), random.randint(0,3), random.randint(0,7), random.randint(0,3), random.randint(0,5),
                primPhoto, otherPhoto, muts
            )

        )
    #    friendDicts =     [
    #                        {'id': 123456789, 'fname': 'Bob', 'lname': 'Newhart', 'name': 'Bob Newhart',
    #                         'gender': 'male', 'age': 63, 'city': 'Chicago', 'state': 'Illinois', 'score': 0.43984,
    #                         'desc': '0 0 0 0 0 0 0 0 0 0'}
    #                    ]*100


    # Actually rank these edges and generate friend dictionaries from them
    edgesRanked = ranking.getFriendRanking(500876410, edgesUnranked, requireOutgoing=False)

    campaign_filterTups = conf.readJson(config['ofa_campaign_config'])
    campaign = "test"
    filterTups = campaign_filterTups.get(campaign, [])
    edgesFiltered = filterEdgesBySec(edgesRanked, filterTups)

    friendDicts = [ e.toDict() for e in edgesFiltered ]
    faceFriends = friendDicts[:6]
    numFace = len(faceFriends)
    allFriends = friendDicts[:25]

    # zzz state = target state with most friends
    state = 'EC'

    targetDict = state_senInfo.get(state)

    msgParams = {
    'msg1_pre' : "Hi there ",
    'msg1_post' : " -- Contact Sen. %s to say you stand with the president on climate legislation!" % targetDict['name'],
    'msg2_pre' : "Now is the time for real climate legislation, ",
    'msg2_post' : "!",
    'msg_other_prompt' : "Checking friends on the left will add tags for them (type around their names):",
    'msg_other_init' : "Replace this text with your message for "
    }

    actionParams =     {
    'fb_action_type' : 'support',
    'fb_object_type' : 'cause',
    'fb_object_url' : 'http://demo.edgeflip.com/ofa_climate/%s' % state
    }
    actionParams.update(fbParams)

    return flask.render_template('ofa_faces_table.html', fbParams=actionParams, msgParams=msgParams, senInfo=targetDict,
                                 face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace)




###########################################################################

if (__name__ == "__main__"):
    if ('--debug' in sys.argv):
        sys.argv.remove('--debug')
        debug = True
    else:
        debug = False
    port = int(sys.argv[1]) if (len(sys.argv) > 1) else 5000
    app.run('0.0.0.0', port=port, debug=debug)


