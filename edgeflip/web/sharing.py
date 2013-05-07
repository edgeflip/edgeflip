#!/usr/bin/python
"""closer to what end user facing webapp should look like

"""

import logging
import flask

from .utils import ajaxResponse, generateSessionId, getIP

from .. import facebook
from .. import ranking
from .. import database
from .. import client_db_tools as cdb
from .. import filtering

from ..settings import config

logger = logging.getLogger(__name__)
app = flask.Flask(__name__)

# Serves just a button, to be displayed in an iframe
@app.route("/button_man/<int:campaignId>/<int:contentId>")
def button_man(campaignId, contentId):
    """serves the button in iframe on client site"""
    # Should be able to get subdomain using the subdomain keyword in app.route()
    # but I was having some trouble getting this to work locally, even setting
    # app.config['SERVER_NAME'] = 'edgeflip.com:8080' -- should probably revisit,
    # but this hack will work for now...
    clientSubdomain = flask.request.host.split('.')[0]
    try:
        clientId = cdb.validateClientSubdomain(campaignId, contentId, clientSubdomain)
    except ValueError as e:
        return "Content not found", 404

    facesURL = cdb.getFacesURL(campaignId, contentId)
    paramsDB = cdb.dbGetClient(clientId, ['fb_app_name','fb_app_id'])[0]
    paramsDict = {'fb_app_name' : paramsDB[0], 'fb_app_id' : int(paramsDB[1])}

    return flask.render_template('button_man.html', fbParams=paramsDict, goto=facesURL)


# Serves the actual faces & share message
@app.route("/frame_faces/<int:campaignId>/<int:contentId>")
def frame_faces(campaignId, contentId):
    """html container (iframe) for client site """
    # zzz As above, do this right (with subdomain keyword)...
    clientSubdomain = flask.request.host.split('.')[0]
    try:
        clientId = cdb.validateClientSubdomain(campaignId, contentId, clientSubdomain)
    except ValueError as e:
        return "Content not found", 404     # Better fallback here or something?

    paramsDB = cdb.dbGetClient(clientId, ['fb_app_name','fb_app_id'])[0]
    paramsDict = {'fb_app_name' : paramsDB[0], 'fb_app_id' : int(paramsDB[1])}

    return flask.render_template('frame_faces.html', fbParams=paramsDict, campaignId=campaignId, contentId=contentId)


@app.route("/faces", methods=['POST'])
def faces():
    """return list of faces - HTML snippet"""
    logger.debug("flask.request.json: %s", str(flask.request.json))
    fbid = int(flask.request.json['fbid'])
    tok = flask.request.json['token']
# TO REMOVE ON TESTING:
#    campaign = flask.request.json.get('campaign')
    numFace = int(flask.request.json['num'])
    sessionId = flask.request.json['sessionid']
    campaignId = flask.request.json['campaignid']
    contentId = flask.request.json['contentid']
    ip = getIP(req = flask.request)

    # zzz As above, do this right (with subdomain keyword)...
    clientSubdomain = flask.request.host.split('.')[0]
    try:
        clientId = cdb.validateClientSubdomain(campaignId, contentId, clientSubdomain)
    except ValueError as e:
        return "Content not found", 404     # Better fallback here or something?

# TO REMOVE ON TESTING:
#    campaign_filterTups = config.ofa_campaigns
#    filterTups = campaign_filterTups.get(campaign, [])

    # Assume we're starting with a short term token, expiring now, then try extending the
    # token. If we hit an error, proceed with what we got from the old one.
    token = datastructs.TokenInfo(tok, fbid, config['fb_app_id'], datetime.datetime.now())
    token = facebook.extendTokenFb(fbid, token) or token

    """next 60 lines or so get pulled out"""
    conn = database.getConn()
    user = database.getUserDb(conn, fbid, config['freshness'], freshnessIncludeEdge=True)

    if (user is not None):  # it's fresh
        logger.debug("user %s is fresh, getting data from db", fbid)
        edgesRanked = ranking.getFriendRankingBestAvailDb(conn, fbid, threshold=0.5)
    else:
        logger.debug("user %s is not fresh, retrieving data from fb", fbid)
        edgesUnranked = facebook.getFriendEdgesFb(fbid, token, requireIncoming=False, requireOutgoing=False)
        edgesRanked = ranking.getFriendRanking(edgesUnranked, requireIncoming=False, requireOutgoing=False)
        user = edgesRanked[0].primary if edgesRanked else facebook.getUserFb(fbid, token)
        database.updateDb(user, token, edgesRanked, background=True)     # zzz should spawn off thread to do db writing
    conn.close()

    # Get filter experiments, do assignment (and write DB)
    filterRecs = cdb.dbGetExperimentTupes('campaign_global_filters', 'campaign_global_filter_id', 'filter_id', [('campaign_id', campaignId)])
    filterExpTupes = [(r[1], r[2]) for r in filterRecs]
    globalFilterId = cdb.doRandAssign(filterExpTupes)
    cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'filter_id', globalFilterId, True, 'campaign_global_filters', [r[0] for r in filterRecs], background=True)

    # apply filter
    globalFilter = cdb.getFilter(globalFilterId)
    filteredEdges = globalFilter.filterEdgesBySec(edgesRanked)

    # Get choice set experiments, do assignment (and write DB)
    choiceSetRecs = cdb.dbGetExperimentTupes('campaign_choice_sets', 'campaign_choice_set_id', 'choice_set_id', [('campaign_id', campaignId)], ['allow_generic', 'generic_url_slug'])
    choiceSetExpTupes = [(r[1], r[2]) for r in choiceSetRecs]
    choiceSetId = cdb.doRandAssign(choiceSetExpTupes)
    cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'choice_set_id', choiceSetId, True, 'campaign_choice_sets', [r[0] for r in filterRecs], background=True)
    allowGeneric = {r[1] : [r[3], r[4]] for r in choiceSetRecs}[choiceSetId]

    # pick best choice set filter (and write DB)
    choiceSet = cdb.getChoiceSet(choiceSetId)
    try:
        bestCSFilter = choiceSet.chooseBestFilter(filteredEdges, useGeneric=allowGeneric[0], minFriends=1, eligibleProportion=1.0)
    except cdb.TooFewFriendsError as e:
        # zzz Here, basically want to check if there's a fallback campaign.
        # zzz If so, we want to recurse on this entire block (filterRecs down).
        # zzz If not, we need to return some error to the user...
        content = 'edgeflip:cause http://allyourfriendsarestateless.com/'
        if (not sessionId):
            sessionId = generateSessionId(ip, content)
        return ajaxResponse('all of your friends are stateless', 200, sessionId)

    friendDicts = [ e.toDict() for e in bestCSFilter[1] ]
    faceFriends = friendDicts[:numFace]
    allFriends = friendDicts[:25]

    choiceSetSlug = bestCSFilter[0].urlSlug if bestCSFilter[0] else allowGeneric[1]

    fbObjectTable = 'campaign_fb_objects'
    fbObjectIdx = 'campaign_fb_object_id'
    fbObjectKeys = [('campaign_id', campaignId)]
    if (bestCSFilter[0] is None):
        # We got generic...
        cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'generic choice set filter', None, False, 'choice_set_filters', [csf.choiceSetFilterId for csf in choiceSet.choiceSetFilters], background=True)
        fbObjectTable = 'campaign_fb_objects'
        fbObjectIdx = 'campaign_fb_object_id'
    else:
        cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'filter_id', bestCSFilter[0].filterId, False, 'choice_set_filters', [csf.choiceSetFilterId for csf in choiceSet.choiceSetFilters], background=True)
        fbObjectKeys = [('campaign_id', campaignId), ('filter_id', bestCSFilter[0].filterId)]

    # Get FB Object experiments, do assignment (and write DB)
    fbObjectRecs = cdb.dbGetExperimentTupes(fbObjectTable, fbObjectIdx, 'fb_object_id', fbObjectKeys)
    fbObjExpTupes = [(r[1], r[2]) for r in fbObjectRecs]
    fbObjectId = int(cdb.doRandAssign(fbObjExpTupes))
    cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'fb_object_id', fbObjectId, True, fbObjectTable, [r[0] for r in fbObjectRecs], background=True)

    # Find template params, return faces
    fbObjectInfo = cdb.dbGetObjectAttributes('fb_object_attributes', 
                    ['og_action', 'og_type', 'sharing_prompt', 
                    'msg1_pre', 'msg1_post', 'msg2_pre', 'msg2_post'], 
                    'fb_object_id', fbObjectId)[0]
    paramsDB = cdb.dbGetClient(clientId, ['fb_app_name','fb_app_id'])[0]

    msgParams = {
        'sharing_prompt' : fbObjectInfo[2],
        'msg1_pre' : fbObjectInfo[3],
        'msg1_post' : fbObjectInfo[4],
        'msg2_pre' : fbObjectInfo[5],
        'msg2_post' : fbObjectInfo[6]
    }
    actionParams = {
        'fb_action_type' : fbObjectInfo[0],
        'fb_object_type' : fbObjectInfo[1],
        'fb_object_url' : flask.url_for('objects', fbObjectId=fbObjectId, contentId=contentId, _external=True) + ('?csslug=%s' % choiceSetSlug if choiceSetSlug else ''),
        'fb_app_name' : paramsDB[0],
        'fb_app_id' : int(paramsDB[1])
    }
    logger.debug('fb_object_url: ' + actionParams['fb_object_url'])

    content = actionParams['fb_app_name']+':'+actionParams['fb_object_type']+' '+actionParams['fb_object_url']
    if (not sessionId):
        sessionId = generateSessionId(ip, content)

    database.writeEventsDb(sessionId, ip, fbid, [f['id'] for f in faceFriends], 'shown', actionParams['fb_app_id'], content, None, background=True)
    return ajaxResponse(flask.render_template('faces_table.html', fbParams=actionParams, msgParams=msgParams,
                                 face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace), 200, sessionId)


# TO REMOVE ON TESTING:
    # bestState = filtering.getBestSecStateFromEdges(edgesRanked, config.ofa_states.keys(), eligibleProportion=1.0)
    # if (bestState is not None):
    #     filterTups.append(('state', 'eq', bestState))
    #     edgesFiltered = filtering.filterEdgesBySec(edgesRanked, filterTups)
    #     logger.debug("have %d edges after filtering on %s", len(edgesFiltered), str(filterTups))

    #     friendDicts = [ e.toDict() for e in edgesFiltered ]
    #     faceFriends = friendDicts[:numFace]
    #     allFriends = friendDicts[:25]

    #     senInfo = config.ofa_states[bestState]

    #     """these messages move into database"""
    #     msgParams = {
    #     'msg1_pre' : "Hi there ",
    #     'msg1_post' : " -- Contact Sen. %s to say you stand with the president on climate legislation!" % senInfo['name'],
    #     'msg2_pre' : "Now is the time for real climate legislation, ",
    #     'msg2_post' : "!",
    #     'msg_other_prompt' : "Checking friends on the left will add tags for them (type around their names):",
    #     'msg_other_init' : "Replace this text with your message for "
    #     }
    #     actionParams =     {
    #     'fb_action_type' : 'support',
    #     'fb_object_type' : 'cause',
    #     'fb_object_url' : flask.url_for('fb_object', state=bestState, _external=True),
    #     'fb_app_name': config.fb_app_name,
    #     'fb_app_id': config.fb_app_id}
        
    #     logger.debug('fb_object_url: ' + actionParams['fb_object_url'])

    #     content = actionParams['fb_app_name']+':'+actionParams['fb_object_type']+' '+actionParams['fb_object_url']
    #     if (not sessionId):
    #         sessionId = generateSessionId(ip, content)

    #     database.writeEventsDb(sessionId, ip, fbid, [f['id'] for f in faceFriends], 'shown', actionParams['fb_app_id'], content, None, background=True)
    #     return ajaxResponse(flask.render_template('faces_table.html', fbParams=actionParams, msgParams=msgParams, senInfo=senInfo,
    #                                  face_friends=faceFriends, all_friends=allFriends, pickFriends=friendDicts, numFriends=numFace), 200, sessionId)

    # else:
    #     content = 'edgeflip:cause http://allyourfriendsarestateless.com/'
    #     if (not sessionId):
    #         sessionId = generateSessionId(ip, content)
    #     return ajaxResponse('all of your friends are stateless', 200, sessionId)


@app.route("/objects/<fbObjectId>/<contentId>")
def objects(fbObjectId, contentId):
    """endpoint linked to on facebook.com

    redirect to client page in JS (b/c this must live on our domain for facebook to crawl)
    """
    fbObjectInfo = cdb.dbGetObjectAttributes('fb_object_attributes', 
                    ['og_action', 'og_type', 'og_title', 'og_image', 'og_description',
                    'page_title', 'url_slug'], 
                    'fb_object_id', fbObjectId)[0]
    clientId = cdb.dbGetObject('fb_objects', ['client_id'], 'fb_object_id', fbObjectId)[0][0]
    paramsDB = cdb.dbGetClient(clientId, ['fb_app_name','fb_app_id'])[0]

    choiceSetSlug = flask.request.args.get('csslug', '')
    fbObjectSlug = fbObjectInfo[6]

    # Determine redirect URL
    redirectURL = cdb.getClientContentURL(contentId, choiceSetSlug, fbObjectSlug)

    objParams = {
    'page_title': fbObjectInfo[5],
    'fb_action_type': fbObjectInfo[0],
    'fb_object_type': fbObjectInfo[1],
    'fb_object_title': fbObjectInfo[2],
    'fb_object_image': fbObjectInfo[3],     # zzz need to figure out if these will all be hosted locally or full URL's in DB
    'fb_object_desc': fbObjectInfo[4],
    'fb_object_url' : flask.url_for('objects', fbObjectId=fbObjectId, contentId=contentId, _external=True) + ('?csslug=%s' % choiceSetSlug if choiceSetSlug else ''),
    'fb_app_name' : paramsDB[0],
    'fb_app_id' : int(paramsDB[1])
    }
    objParams.update(fbParams)

    return flask.render_template('fb_object.html', fbParams=objParams, redirectURL=redirectURL)


# TO REMOVE ON TESTING:
# @app.route("/fb_object")
# def fb_object():
#     """endpoint linked to on facebook.com

#     redirect to client page in JS (b/c this must live on our domain for facebook to crawl)
#     """
#     state = flask.request.args.get('state')
#     if state is None:
#         return "No state specified", 404
    
#     senInfo = config.ofa_states.get(state)
#     if (not senInfo):
#         return "Whoopsie! No targets in that state.", 404  # you know, or some 404 page...

#     objParams = {
#     'page_title': "Tell Sen. %s We're Putting Denial on Trial!" % senInfo['name'],
#     'fb_action_type': 'support',
#     'fb_object_type': 'cause',
#     'fb_object_title': 'Climate Legislation',
#     'fb_object_image': 'http://demo.edgeflip.com/' + flask.url_for('static', filename='doc_brown.jpg'),
#     'fb_object_desc': "The time has come for real climate legislation in America. Tell Senator %s that you stand with President Obama and Organizing for Action on this important issue. We can't wait one more day to act." % senInfo['name'],
#     'fb_object_url' : flask.url_for('fb_object', state=state, _external=True),
#     'fb_app_name': config.fb_app_name,
#     'fb_app_id': config.fb_app_id
#     }

#     # zzz Are we going to want/need to pass URL parameters to this redirect?
#     redirectURL = config.web.fb_object_redirect

#     return flask.render_template('fb_object.html', fbParams=objParams, redirectURL=redirectURL)


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
