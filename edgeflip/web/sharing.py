#!/usr/bin/python
"""closer to what end user facing webapp should look like

"""

import logging
import flask
import datetime
import time
import random

from .utils import ajaxResponse, generateSessionId, getIP, locateTemplate

from .. import facebook
from .. import mock_facebook
from .. import ranking
from .. import database
from .. import datastructs
from .. import client_db_tools as cdb
from .. import filtering

from ..settings import config

logger = logging.getLogger(__name__)
app = flask.Flask(__name__)

MAX_FALLBACK_COUNT = 3      # move to config (or do we want it hard-coded)??

# Serves just a button, to be displayed in an iframe
@app.route("/button/<int:campaignId>/<int:contentId>")
def button(campaignId, contentId):
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

    ip = getIP(req = flask.request)
    sessionId = generateSessionId(ip, '%s:button %s' % (paramsDict['fb_app_name'], facesURL))

    # Get button style experiments (if any), do assignment (and write DB)
    styleTemplate = None
    try:
        styleRecs = cdb.dbGetExperimentTupes('campaign_button_styles', 'campaign_button_style_id', 'button_style_id', [('campaign_id', campaignId)])
        styleExpTupes = [(r[1], r[2]) for r in styleRecs]
        styleId = int(cdb.doRandAssign(styleExpTupes))
        cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'button_style_id', styleId, True, 'campaign_button_styles', [r[0] for r in styleRecs], background=config.database.use_threads)

        # Find template location
        styleTemplate = cdb.dbGetObjectAttributes('button_style_files', 
                        ['html_template'], 'button_style_id', styleId)[0][0]
    except Exception as e:
        # Weren't able to get a style from the DB, so fall back to default
        # zzz (mostly a quick hack to account for existing clients without specific button style in in the DB...)
        styleTemplate = locateTemplate('button.html', clientSubdomain, app)

    return flask.render_template(styleTemplate, fbParams=paramsDict, goto=facesURL, campaignId=campaignId, contentId=contentId, sessionId=sessionId)


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

    thanksURL, errorURL = cdb.dbGetObjectAttributes('campaign_properties', ['client_thanks_url', 'client_error_url'], 'campaign_id', campaignId)[0]

    paramsDB = cdb.dbGetClient(clientId, ['fb_app_name','fb_app_id'])[0]
    paramsDict = {'fb_app_name' : paramsDB[0], 'fb_app_id' : int(paramsDB[1])}

    return flask.render_template(locateTemplate('frame_faces.html', clientSubdomain, app), fbParams=paramsDict, 
                                campaignId=campaignId, contentId=contentId,
                                thanksURL=thanksURL, errorURL=errorURL)


@app.route("/faces", methods=['POST'])
def faces():
    """return list of faces - HTML snippet"""
    logger.debug("flask.request.json: %s", str(flask.request.json))
    fbid = int(flask.request.json['fbid'])
    tok = flask.request.json['token']
    numFace = int(flask.request.json['num'])
    sessionId = flask.request.json['sessionid']
    campaignId = flask.request.json['campaignid']
    contentId = flask.request.json['contentid']
    mockMode = True if flask.request.json.get('mockmode') else False
    ip = getIP(req = flask.request)

    fbmodule = None
    if (mockMode):
        logger.info('Running in mock mode')
        fbmodule = mock_facebook
        # Generate a random fake ID for our primary to avoid collisions in DB
        fbid = 100000000000+random.randint(1,10000000)
    else:
        fbmodule = facebook

    # zzz As above, do this right (with subdomain keyword)...
    clientSubdomain = flask.request.host.split('.')[0]
    try:
        clientId = cdb.validateClientSubdomain(campaignId, contentId, clientSubdomain)
    except ValueError as e:
        return "Content not found", 404     # Better fallback here or something?

    # Want to ensure mock mode can only be run in staging or local development
    if (mockMode and not (clientSubdomain == config.web.mock_subdomain)):
        return "Mock mode only allowed for the mock client.", 403

    paramsDB = cdb.dbGetClient(clientId, ['fb_app_name','fb_app_id'])[0]

    if (not sessionId):
        # If we don't have a sessionId, generate one with "content" as the button that would have pointed to this page...
        thisContent = '%s:button %s' % (paramsDB[0], flask.url_for('frame_faces', campaignId=campaignId, contentId=contentId, _external=True))
        sessionId = generateSessionId(ip, thisContent)

    # Assume we're starting with a short term token, expiring now, then try extending the
    # token. If we hit an error, proceed with what we got from the old one.
    token = datastructs.TokenInfo(tok, fbid, int(paramsDB[1]), datetime.datetime.now())
    token = fbmodule.extendTokenFb(fbid, token, int(paramsDB[1])) or token

    """next 60 lines or so get pulled out"""

    user = None
    if (not mockMode):
        user = database.getUserDb(fbid, config.freshness, freshnessIncludeEdge=False)

    edgesUnranked = None
    if (user is not None): # user is there, but may have come in as a secondary (and therefore have no edges)
        logger.debug("user %s is fresh, getting data from db", fbid)
        newerThan = time.time() - config.freshness*24*60*60 # newerThan is a unix timestamp to restict edges pulled from DB
        edgesUnranked = database.getFriendEdgesDb(fbid, requireOutgoing=False, newerThan=newerThan)
        # zzz Even if we got the user from the DB, we'll still want to at least write
        #     the token for two reasons: (1) we can update its expiration date since
        #     it will have been extended because they came back, and (2) it's possible
        #     we got this user associated with a different Facebook app id, so want to
        #     be sure the new association is stored!

    # zzz This logic depends heavily on the fact that we're using soley px3 right now
    #     (and requireOutgoing is always False above). Otherwise, the edges may have
    #     various updated dates and we could only have a small subset of them here.
    #     (I kinda at least want to know the number of friends to compare to...)
    #     We really need a better way of doing this!!!
    edgesRanked = None
    if (not edgesUnranked):
        logger.debug("edges or user info for user %s is not fresh, retrieving data from fb", fbid)
        user = fbmodule.getUserFb(fbid, token.tok)
        edgesUnranked = fbmodule.getFriendEdgesFb(fbid, token.tok, requireIncoming=False, requireOutgoing=False)
        edgesRanked = ranking.getFriendRanking(edgesUnranked, requireIncoming=False, requireOutgoing=False)
        database.updateDb(user, token, edgesRanked, background=config.database.use_threads)
    else:
        edgesRanked = ranking.getFriendRanking(edgesUnranked, requireIncoming=False, requireOutgoing=False)

    # Outside the if block because we want to do this regardless of whether we got
    # user data from the DB (since they could be connecting with a new client even
    # though we already have them in the DB associated with someone else)
    cdb.dbWriteUserClient(fbid, clientId, background=config.database.use_threads)

    return applyCampaign(edgesRanked, clientSubdomain, campaignId, contentId, sessionId, ip, fbid, numFace, paramsDB)


def applyCampaign(edgesRanked, clientSubdomain, campaignId, contentId, sessionId, ip, fbid, numFace, paramsDB, fallbackCount=0):
    """Do the work of applying campaign properties to a set of edges.
    May recursively call itself upon falling back, up to MAX_FALLBACK_COUNT times.

    Should move out of the flask app soon...
    """

    if (fallbackCount > MAX_FALLBACK_COUNT):
        raise RuntimeError("Exceeded maximum fallback count")
    
    # Check if any friends should be excluded for this campaign/content combination
    excludeFriends = database.getFaceExclusionsDb(fbid, campaignId, contentId)
    edgesEligible = [e for e in edgesRanked if e.secondary.id not in excludeFriends]

    # Get filter experiments, do assignment (and write DB)
    filterRecs = cdb.dbGetExperimentTupes('campaign_global_filters', 'campaign_global_filter_id', 'filter_id', [('campaign_id', campaignId)])
    filterExpTupes = [(r[1], r[2]) for r in filterRecs]
    globalFilterId = cdb.doRandAssign(filterExpTupes)
    cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'filter_id', globalFilterId, True, 'campaign_global_filters', [r[0] for r in filterRecs], background=config.database.use_threads)

    # apply filter
    globalFilter = cdb.getFilter(globalFilterId)
    filteredEdges = globalFilter.filterEdgesBySec(edgesEligible)

    # Get choice set experiments, do assignment (and write DB)
    choiceSetRecs = cdb.dbGetExperimentTupes('campaign_choice_sets', 'campaign_choice_set_id', 'choice_set_id', [('campaign_id', campaignId)], ['allow_generic', 'generic_url_slug'])
    choiceSetExpTupes = [(r[1], r[2]) for r in choiceSetRecs]
    choiceSetId = cdb.doRandAssign(choiceSetExpTupes)
    cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'choice_set_id', choiceSetId, True, 'campaign_choice_sets', [r[0] for r in filterRecs], background=config.database.use_threads)
    allowGeneric = {r[1] : [r[3], r[4]] for r in choiceSetRecs}[choiceSetId]

    # pick best choice set filter (and write DB)
    choiceSet = cdb.getChoiceSet(choiceSetId)
    try:
        bestCSFilter = choiceSet.chooseBestFilter(filteredEdges, useGeneric=allowGeneric[0], minFriends=1, eligibleProportion=1.0)
    except cdb.TooFewFriendsError as e:
        logger.info("Too few friends found for %s with campaign %s. Checking for fallback." % (fbid, campaignId))

        # Get fallback campaign_id and content_id from DB
        cmpgPropsId, fallbackCampaignId, fallbackContentId = cdb.dbGetObjectAttributes('campaign_properties', ['campaign_property_id', 'fallback_campaign_id', 'fallback_content_id'], 'campaign_id', campaignId)[0]
        # if fallback campaign_id IS NULL, nothing we can do, so just return an error.
        if (fallbackCampaignId is None):
            # zzz Obviously, do something smarter here...
            logger.info("No fallback for %s with campaign %s. Returning error to user." % (fbid, campaignId))
            thisContent = '%s:button %s' % (paramsDB[0], flask.url_for('frame_faces', campaignId=campaignId, contentId=contentId, _external=True))
            database.writeEventsDb(sessionId, campaignId, contentId, ip, fbid, [None], 'no_friends_error', int(paramsDB[1]), thisContent, None, background=config.database.use_threads)
            return ajaxResponse('No friends identified for you.', 500, sessionId)

        # if fallback content_id IS NULL, defer to current content_id
        if (fallbackContentId is None):
            fallbackContentId = contentId

        # write "fallback" assignments to DB
        cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'fallback campaign', fallbackCampaignId, False, 'campaign_properties', [cmpgPropsId], background=config.database.use_threads)
        cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'fallback content', fallbackContentId, False, 'campaign_properties', [cmpgPropsId], background=config.database.use_threads)

        # Recursive call with new fallbackCampaignId & fallbackContentId, incrementing fallbackCount
        return applyCampaign(edgesRanked, clientSubdomain, fallbackCampaignId, fallbackContentId, sessionId, ip, fbid, numFace, paramsDB, fallbackCount+1)

    friendDicts = [ e.toDict() for e in bestCSFilter[1] ]
    faceFriends = friendDicts[:numFace]     # The first set to be shown as faces
    allFriends = friendDicts[:50]           # Anyone who we might show as a face. Totally arbitrary number to avoid going too far down the list, but maybe just send them all?
    pickDicts = [ e.toDict() for e in edgesRanked ] # For the "manual add" box -- ALL friends can be included, regardless of targeting criteria or prior shares/suppressions!

    choiceSetSlug = bestCSFilter[0].urlSlug if bestCSFilter[0] else allowGeneric[1]

    fbObjectTable = 'campaign_fb_objects'
    fbObjectIdx = 'campaign_fb_object_id'
    fbObjectKeys = [('campaign_id', campaignId)]
    if (bestCSFilter[0] is None):
        # We got generic...
        logger.debug("Generic returned for %s with campaign %s." % (fbid, campaignId))
        cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'generic choice set filter', None, False, 'choice_set_filters', [csf.choiceSetFilterId for csf in choiceSet.choiceSetFilters], background=config.database.use_threads)
        fbObjectTable = 'campaign_fb_objects'
        fbObjectIdx = 'campaign_fb_object_id'
    else:
        cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'filter_id', bestCSFilter[0].filterId, False, 'choice_set_filters', [csf.choiceSetFilterId for csf in choiceSet.choiceSetFilters], background=config.database.use_threads)
        fbObjectKeys = [('campaign_id', campaignId), ('filter_id', bestCSFilter[0].filterId)]

    # Get FB Object experiments, do assignment (and write DB)
    fbObjectRecs = cdb.dbGetExperimentTupes(fbObjectTable, fbObjectIdx, 'fb_object_id', fbObjectKeys)
    fbObjExpTupes = [(r[1], r[2]) for r in fbObjectRecs]
    fbObjectId = int(cdb.doRandAssign(fbObjExpTupes))
    cdb.dbWriteAssignment(sessionId, campaignId, contentId, 'fb_object_id', fbObjectId, True, fbObjectTable, [r[0] for r in fbObjectRecs], background=config.database.use_threads)

    # Find template params, return faces
    fbObjectInfo = cdb.dbGetObjectAttributes('fb_object_attributes', 
                    ['og_action', 'og_type', 'sharing_prompt', 
                    'msg1_pre', 'msg1_post', 'msg2_pre', 'msg2_post', 'og_title', 'og_image', 'og_description'],
                    'fb_object_id', fbObjectId)[0]

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
        'fb_app_id' : int(paramsDB[1]),
        'fb_object_title' : fbObjectInfo[7],
        'fb_object_image' : fbObjectInfo[8],
        'fb_object_description' : fbObjectInfo[9]
    }
    logger.debug('fb_object_url: ' + actionParams['fb_object_url'])

    content = actionParams['fb_app_name']+':'+actionParams['fb_object_type']+' '+actionParams['fb_object_url']
    if (not sessionId):
        sessionId = generateSessionId(ip, content)

    database.writeEventsDb(sessionId, campaignId, contentId, ip, fbid, [f['id'] for f in faceFriends], 'shown', actionParams['fb_app_id'], content, None, background=config.database.use_threads)

    return ajaxResponse(flask.render_template(locateTemplate('faces_table.html', clientSubdomain, app), fbParams=actionParams, msgParams=msgParams,
                                 face_friends=faceFriends, all_friends=allFriends, pickFriends=pickDicts, numFriends=numFace), 200, sessionId)


@app.route("/objects/<fbObjectId>/<contentId>")
def objects(fbObjectId, contentId):
    """endpoint linked to on facebook.com

    redirect to client page in JS (b/c this must live on our domain for facebook to crawl)
    """
    clientId = cdb.dbGetObject('fb_objects', ['client_id'], 'fb_object_id', fbObjectId)
    if (not clientId):
        return "404 - Content Not Found", 404
    else:
        clientId = clientId[0][0]

    fbObjectInfo = cdb.dbGetObjectAttributes('fb_object_attributes', 
                    ['og_action', 'og_type', 'og_title', 'og_image', 'og_description',
                    'page_title', 'url_slug'], 
                    'fb_object_id', fbObjectId)
    paramsDB = cdb.dbGetClient(clientId, ['fb_app_name','fb_app_id'])

    if (not fbObjectInfo or not paramsDB):
        return "404 - Content Not Found", 404
    else:
        fbObjectInfo = fbObjectInfo[0]
        paramsDB = paramsDB[0]

    choiceSetSlug = flask.request.args.get('csslug', '')
    actionId = flask.request.args.get('fb_action_ids', '').split(',')[0].strip()
        # Note: could potentially be a comma-delimited list, but shouldn't be in our case...
    actionId = int(actionId) if actionId else None

    fbObjectSlug = fbObjectInfo[6]

    # Determine redirect URL
    redirectURL = cdb.getClientContentURL(contentId, choiceSetSlug, fbObjectSlug)

    if (not redirectURL):
        return "404 - Content Not Found", 404

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

    ip = getIP(req = flask.request)
    sessionId = flask.request.args.get('efsid')
    content = '%(fb_app_name)s:%(fb_object_type)s %(fb_object_url)s' % objParams
    if (not sessionId):
        sessionId = generateSessionId(ip, content)

    # record the clickback event to the DB
    database.writeEventsDb(sessionId, None, contentId, ip, None, [None], 'clickback', objParams['fb_app_id'], content, actionId, background=config.database.use_threads)

    return flask.render_template('fb_object.html', fbParams=objParams, redirectURL=redirectURL, contentId=contentId)


@app.route('/suppress', methods=['POST'])
def suppress():
    """called when user declines a friend. returns a new friend (HTML snippet)

    """
    userid = flask.request.json['userid']
    appid = flask.request.json['appid']
    campaignId = flask.request.json['campaignid'] # This is an ID in our client DB schema
    contentId = flask.request.json['contentid'] # Also an ID in our client DB schema
    content = flask.request.json['content']     # This is a string with type & URL as passed to FB
    oldid = flask.request.json['oldid']
    sessionId = flask.request.json['sessionid']
    ip = getIP(req = flask.request)

    newid = flask.request.json['newid']
    fname = flask.request.json['fname']
    lname = flask.request.json['lname']

    if (not sessionId):
        sessionId = generateSessionId(ip, content)

    database.writeEventsDb(sessionId, campaignId, contentId, ip, userid, [oldid], 'suppressed', appid, content, None, background=config.database.use_threads)
    database.writeFaceExclusionsDb(userid, campaignId, contentId, [oldid], 'suppressed', background=config.database.use_threads)

    if (newid != ''):
        database.writeEventsDb(sessionId, campaignId, contentId, ip, userid, [newid], 'shown', appid, content, None, background=config.database.use_threads)
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
    campaignId = flask.request.json.get('campaignid')
    contentId = flask.request.json.get('contentid')
    content = flask.request.json['content']
    actionId = flask.request.json.get('actionid')
    actionId = actionId or None     # might get empty string from ajax...
    friends = [ int(f) for f in flask.request.json.get('friends', []) ]
    friends = friends or [None]
    eventType = flask.request.json['eventType']
    sessionId = flask.request.json['sessionid']
    ip = getIP(req = flask.request)

    if (eventType not in [  'button_load', 'button_click', 
                            'authorized', 'auth_fail', 
                            'select_all_click', 'suggest_message_click', 
                            'share_click', 'share_fail', 'shared', 'clickback'
                        ]):
        return "Ah, ah, ah. You didn't say the magic word.", 403

    # For authorized events, write the user-client connection
    # (can't just do in the faces endpoint because we'll run auth-only campaigns, too)
    if (eventType == 'authorized'):
        clientId = cdb.dbGetObject('campaigns', ['client_id'], 'campaign_id', campaignId)
        if (clientId):
            clientId = clientId[0][0]
            cdb.dbWriteUserClient(userId, clientId, background=config.database.use_threads)

    if (eventType == 'shared'):
        # If this was a share, write these friends to the exclusions table so we don't show them for the same content/campaign again
        database.writeFaceExclusionsDb(userId, campaignId, contentId, friends, 'shared', background=config.database.use_threads)

    if (not sessionId):
        sessionId = generateSessionId(ip, content)

    errorMsg = flask.request.json.get('errorMsg')
    if (errorMsg):
        # may want to push these to the DB at some point, but at least for now,
        # dump them to the logs to ensure we keep the data.
        logger.error('Front-end error encountered for user %s in session %s: %s', userId, sessionId, errorMsg)

    shareMsg = flask.request.json.get('shareMsg')
    if (shareMsg):
        database.writeShareMsgDb(actionId, userId, campaignId, contentId, shareMsg, background=config.database.use_threads)

    database.writeEventsDb(sessionId, campaignId, contentId, ip, userId, friends, eventType, appId, content, actionId, background=config.database.use_threads)
    return ajaxResponse('', 200, sessionId)

@app.route("/canvas/", methods=['GET', 'POST'])
def canvas():
    """Quick splash page for Facebook Canvas"""

    return flask.render_template('canvas.html')


@app.route("/health_check")
def health_check():
    """ELB status
    
    - if called as `/health_check?elb` just return 200
    - if called as `/health_check` return a JSON dict with status of various component
    
    """
    if 'elb' in flask.request.args:
        return "It's Alive!", 200

    components = {'database': False,
                  'facebook': False}

    # Make sure we can connect and return results from DB
    conn = database.getConn()
    try:
        curs = conn.cursor()
        curs.execute("SELECT 1+1")
        if curs.fetchone()[0] == 2:
            components['database'] = True
    finally:
        conn.rollback()

    # Make sure we can talk to FB and get simple user info back
    try:
        fbresp = facebook.getUrlFb("http://graph.facebook.com/6963")
        if int(fbresp['id']) == 6963:
            components['facebook'] = True
    except:
        # xxx do something more intelligent here?
        raise
    
    return flask.jsonify(components)

