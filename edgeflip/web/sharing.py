#!/usr/bin/python
"""closer to what end user facing webapp should look like

"""

import logging
import flask
import datetime
import random
import json

from .utils import ajaxResponse, generateSessionId, getIP, locateTemplate, decodeDES

from .. import facebook
from .. import mock_facebook
from .. import database
from .. import datastructs
from .. import client_db_tools as cdb
from edgeflip import tasks, celery

from ..settings import config

logger = logging.getLogger(__name__)
app = flask.Flask(__name__)


@app.route("/button/<campaignSlug>")
def button_encoded(campaignSlug):
    """Endpoint to serve buttons with obfuscated URL"""

    try:
        decoded = decodeDES(campaignSlug)
        campaignId, contentId = [int(i) for i in decoded.split('/')]
    except Exception as e:
        logger.error("Exception on decrypting button: %s", str(e))
        return "Content not found", 404

    return button(campaignId, contentId)


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
    except ValueError:
        return "Content not found", 404

    facesURL = cdb.getFacesURL(campaignId, contentId)
    paramsDB = cdb.dbGetClient(clientId, ['fb_app_name', 'fb_app_id'])[0]
    paramsDict = {'fb_app_name': paramsDB[0], 'fb_app_id': int(paramsDB[1])}

    ip = getIP(req=flask.request)
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
    except Exception:
        # Weren't able to get a style from the DB, so fall back to default
        # zzz (mostly a quick hack to account for existing clients without specific button style in in the DB...)
        styleTemplate = locateTemplate('button.html', clientSubdomain, app)

    return flask.render_template(styleTemplate, fbParams=paramsDict, goto=facesURL, campaignId=campaignId, contentId=contentId, sessionId=sessionId)


@app.route("/frame_faces/<campaignSlug>")
def frame_faces_encoded(campaignSlug):
    """Endpoint to serve buttons with obfuscated URL"""

    try:
        decoded = decodeDES(campaignSlug)
        campaignId, contentId = [int(i) for i in decoded.split('/')]
    except Exception as e:
        logger.error("Exception on decrypting frame_faces: %s", str(e))
        return "Content not found", 404

    return frame_faces(campaignId, contentId)


# Serves the actual faces & share message
@app.route("/frame_faces/<int:campaignId>/<int:contentId>")
def frame_faces(campaignId, contentId):
    """html container (iframe) for client site """
    # zzz As above, do this right (with subdomain keyword)...
    clientSubdomain = flask.request.host.split('.')[0]
    try:
        clientId = cdb.validateClientSubdomain(campaignId, contentId, clientSubdomain)
    except ValueError:
        return "Content not found", 404     # Better fallback here or something?

    test_mode = False
    test_fbid = test_token = None
    if 'test_mode' in flask.request.args:
        test_mode = True
        if 'fbid' not in flask.request.args or 'token' not in flask.request.args:
            return "Test mode requires an ID and Token", 400
        test_fbid = int(flask.request.args['fbid'])
        test_token = flask.request.args['token']

    thanksURL, errorURL = cdb.dbGetObjectAttributes('campaign_properties', ['client_thanks_url', 'client_error_url'], 'campaign_id', campaignId)[0]

    paramsDB = cdb.dbGetClient(clientId, ['fb_app_name', 'fb_app_id'])[0]
    paramsDict = {'fb_app_name': paramsDB[0], 'fb_app_id': int(paramsDB[1])}

    return flask.render_template(
        locateTemplate('frame_faces.html', clientSubdomain, app),
        fbParams=paramsDict,
        campaignId=campaignId,
        contentId=contentId,
        thanksURL=thanksURL,
        errorURL=errorURL,
        app_version=config.app_version,
        test_mode=test_mode,
        test_fbid=test_fbid,
        test_token=test_token
    )


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
    px3_task_id = flask.request.json.get('px3_task_id')
    px4_task_id = flask.request.json.get('px4_task_id')
    last_call = True if flask.request.json.get('last_call') else False
    ip = getIP(req=flask.request)
    fbmodule = None
    edgesRanked = None

    fbmodule = None
    if (mockMode):
        logger.info('Running in mock mode')
        fbmodule = mock_facebook
        # Generate a random fake ID for our primary to avoid collisions in DB
        fbid = 100000000000 + random.randint(1, 10000000)
    else:
        fbmodule = facebook

    # zzz As above, do this right (with subdomain keyword)...
    clientSubdomain = flask.request.host.split('.')[0]
    try:
        clientId = cdb.validateClientSubdomain(campaignId, contentId, clientSubdomain)
    except ValueError:
        return "Content not found", 404     # Better fallback here or something?

    # Want to ensure mock mode can only be run in staging or local development
    if (mockMode and not (clientSubdomain == config.web.mock_subdomain)):
        return "Mock mode only allowed for the mock client.", 403

    paramsDB = cdb.dbGetClient(clientId, ['fb_app_name', 'fb_app_id'])[0]

    if (not sessionId):
        # If we don't have a sessionId, generate one with "content" as the button that would have pointed to this page...
        thisContent = '%s:button %s' % (paramsDB[0], flask.url_for('frame_faces', campaignId=campaignId, contentId=contentId, _external=True))
        sessionId = generateSessionId(ip, thisContent)

    if px3_task_id and px4_task_id:
        px3_result = celery.celery.AsyncResult(px3_task_id)
        px4_result = celery.celery.AsyncResult(px4_task_id)
        if (px3_result.ready() and (px4_result.ready() or last_call)):
            px4_edges = px4_result.result if px4_result.successful() else []
            edgesRanked, edgesFiltered, bestCSFilterId, choiceSetSlug, campaignId, contentId = px3_result.result
            if not all([edgesRanked, edgesFiltered]):
                return ajaxResponse('No friends identified for you.', 500, sessionId)
        else:
            if last_call and not px3_result.ready():
                return ajaxResponse('No friends identified for you.', 500, sessionId)
            else:
                return ajaxResponse(
                    json.dumps({
                        'status': 'waiting',
                        'px3_task_id': px3_task_id,
                        'px4_task_id': px4_task_id,
                        'campaignid': campaignId,
                        'contentid': contentId,
                    }),
                    200,
                    sessionId
                )
    else:

        # Assume we're starting with a short term token, expiring now, then try extending the
        # token. If we hit an error, proceed with what we got from the old one.
        token = datastructs.TokenInfo(tok, fbid, int(paramsDB[1]), datetime.datetime.now())
        token = fbmodule.extendTokenFb(fbid, token, int(paramsDB[1])) or token

        px3_task_id = tasks.proximity_rank_three(
            mockMode=mockMode,
            token=token,
            clientSubdomain=clientSubdomain,
            campaignId=campaignId,
            contentId=contentId,
            sessionId=sessionId,
            ip=ip,
            fbid=fbid,
            numFace=numFace,
            paramsDB=paramsDB
        )
        px4_task = tasks.proximity_rank_four.delay(
            mockMode, fbid, token)
        return ajaxResponse(
            json.dumps({
                'status': 'waiting',
                'px3_task_id': px3_task_id,
                'px4_task_id': px4_task.id,
                'campaignid': campaignId,
                'contentid': contentId,
            }),
            200,
            sessionId
        )

    # Outside the if block because we want to do this regardless of whether we got
    # user data from the DB (since they could be connecting with a new client even
    # though we already have them in the DB associated with someone else)
    cdb.dbWriteUserClient(fbid, clientId, background=config.database.use_threads)
    if px4_edges:
        edgesFiltered.rerankEdges(px4_edges)

    return applyCampaign(
        edgesRanked, edgesFiltered, bestCSFilterId, choiceSetSlug,
        clientSubdomain, campaignId, contentId, sessionId, ip,
        fbid, numFace, paramsDB
    )


def applyCampaign(edgesRanked, edgesFiltered, bestCSFilterId, choiceSetSlug,
                  clientSubdomain, campaignId, contentId, sessionId,
                  ip, fbid, numFace, paramsDB):
    ''' Receives the filtered edges, the filters used, and all the necessary
    information needed to record the campaign assignment.
    '''
    MAX_FACES = 50  # Totally arbitrary number to avoid going too far down the list.

    # FIXME: edgesRanked is actually just px3 ranked right now!
    friendDicts = [e.toDict() for e in edgesFiltered.edges()]
    faceFriends = friendDicts[:numFace]            # The first set to be shown as faces
    allFriends = friendDicts[:MAX_FACES]           # Anyone who we might show as a face.
    pickDicts = [e.toDict() for e in edgesRanked]  # For the "manual add" box -- ALL friends can be included, regardless of targeting criteria or prior shares/suppressions!

    fbObjectTable = 'campaign_fb_objects'
    fbObjectIdx = 'campaign_fb_object_id'
    fbObjectKeys = [('campaign_id', campaignId)]
    if (bestCSFilterId is None):
        # We got generic...
        fbObjectTable = 'campaign_generic_fb_objects'
        fbObjectIdx = 'campaign_generic_fb_object_id'
    else:
        fbObjectKeys = [
            ('campaign_id', campaignId),
            ('filter_id', bestCSFilterId)
        ]

    # Get FB Object experiments, do assignment (and write DB)
    fbObjectRecs = cdb.dbGetExperimentTupes(
        fbObjectTable, fbObjectIdx, 'fb_object_id', fbObjectKeys
    )
    fbObjExpTupes = [(r[1], r[2]) for r in fbObjectRecs]
    fbObjectId = int(cdb.doRandAssign(fbObjExpTupes))
    cdb.dbWriteAssignment(
        sessionId, campaignId, contentId, 'fb_object_id', fbObjectId,
        True, fbObjectTable, [r[0] for r in fbObjectRecs],
        background=config.database.use_threads
    )

    # Find template params, return faces
    fbObjectInfo = cdb.dbGetObjectAttributes(
        'fb_object_attributes',
        [
            'og_action', 'og_type', 'sharing_prompt',
            'msg1_pre', 'msg1_post', 'msg2_pre', 'msg2_post',
            'og_title', 'og_image', 'og_description'
        ],
        'fb_object_id', fbObjectId)[0]

    msgParams = {
        'sharing_prompt': fbObjectInfo[2],
        'msg1_pre': fbObjectInfo[3],
        'msg1_post': fbObjectInfo[4],
        'msg2_pre': fbObjectInfo[5],
        'msg2_post': fbObjectInfo[6]
    }
    actionParams = {
        'fb_action_type': fbObjectInfo[0],
        'fb_object_type': fbObjectInfo[1],
        'fb_object_url': flask.url_for(
            'objects', fbObjectId=fbObjectId,
            contentId=contentId, _external=True) + (
                '?csslug=%s' % choiceSetSlug if choiceSetSlug else ''
            ),
        'fb_app_name': paramsDB[0],
        'fb_app_id': int(paramsDB[1]),
        'fb_object_title': fbObjectInfo[7],
        'fb_object_image': fbObjectInfo[8],
        'fb_object_description': fbObjectInfo[9]
    }
    logger.debug('fb_object_url: ' + actionParams['fb_object_url'])

    content = actionParams['fb_app_name'] + ':' + actionParams['fb_object_type'] + ' ' + actionParams['fb_object_url']
    if (not sessionId):
        sessionId = generateSessionId(ip, content)

    # Write "generated" events to the DB for all the friends that
    # could get shown to track which campaign they were generated
    # under. In the case of cascading fallbacks, this could actually
    # differ from the final campaign used for the shown/shared events.
    numGen = MAX_FACES
    for tier in edgesFiltered.tiers:
        edges_list = tier['edges'][:]
        tier_campaignId = tier['campaignId']
        tier_contentId = tier['contentId']

        if len(edges_list) > numGen:
            edges_list = edges_list[:numGen]

        if (edges_list):
            database.writeEventsDb(
                sessionId, tier_campaignId, tier_contentId, ip, fbid,
                [e.secondary.id for e in edges_list], 'generated',
                actionParams['fb_app_id'], content, None,
                background=config.database.use_threads
            )
            numGen = numGen - len(edges_list)

        if (numGen <= 0):
            break

    database.writeEventsDb(
        sessionId, campaignId, contentId, ip, fbid,
        [f['id'] for f in faceFriends], 'shown',
        actionParams['fb_app_id'], content, None,
        background=config.database.use_threads
    )

    return ajaxResponse(
        json.dumps({
            'status': 'success',
            'html': flask.render_template(
                locateTemplate('faces_table.html', clientSubdomain, app),
                fbParams=actionParams, msgParams=msgParams,
                face_friends=faceFriends, all_friends=allFriends,
                pickFriends=pickDicts, numFriends=numFace
            ),
            'campaignid': campaignId,
            'contentid': contentId,
        }), 200, sessionId)


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
    paramsDB = cdb.dbGetClient(clientId, ['fb_app_name', 'fb_app_id'])

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
        'fb_object_image': fbObjectInfo[3],
        'fb_object_desc': fbObjectInfo[4],
        'fb_object_url': flask.url_for('objects', fbObjectId=fbObjectId, contentId=contentId, _external=True) + ('?csslug=%s' % choiceSetSlug if choiceSetSlug else ''),
        'fb_app_name': paramsDB[0],
        'fb_app_id': int(paramsDB[1])
    }

    ip = getIP(req=flask.request)
    sessionId = flask.request.args.get('efsid')
    content = '%(fb_app_name)s:%(fb_object_type)s %(fb_object_url)s' % objParams
    if (not sessionId):
        sessionId = generateSessionId(ip, content)

    userAgent = flask.request.user_agent.string
    if (userAgent.find('facebookexternalhit') != -1):
        # It's just the FB crawler! Note it in the logs, but don't write the event
        logger.info("Facebook crawled object %s with content %s from IP %s", fbObjectId, contentId, ip)
    else:
        if not actionId:
            logger.error("Clickback with no action_id (writing the event anyway) from URL: %s", flask.request.url)
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
    ip = getIP(req=flask.request)

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
    friends = [int(f) for f in flask.request.json.get('friends', [])]
    friends = friends or [None]
    eventType = flask.request.json['eventType']
    sessionId = flask.request.json['sessionid']
    ip = getIP(req=flask.request)

    if (eventType not in ['button_load', 'button_click',
                            'authorized', 'auth_fail',
                            'select_all_click', 'suggest_message_click',
                            'share_click', 'share_fail', 'shared', 'clickback'
                        ]):
        return "Ah, ah, ah. You didn't say the magic word.", 403

    if (not sessionId):
        sessionId = generateSessionId(ip, content)

    # Write the event itself (do this first, so at least we record it even if there's an error below!)
    database.writeEventsDb(sessionId, campaignId, contentId, ip, userId, friends, eventType, appId, content, actionId, background=config.database.use_threads)

    # For authorized events, write the user-client connection & token
    # (can't just do in the faces endpoint because we'll run auth-only campaigns, too)
    if (eventType == 'authorized'):
        tok = flask.request.json.get('token')
        clientId = cdb.dbGetObject('campaigns', ['client_id'], 'campaign_id', campaignId)
        if (clientId):

            # associate the user with this client
            clientId = clientId[0][0]
            cdb.dbWriteUserClient(userId, clientId, background=config.database.use_threads)

            # extend & record their access token (creating a 'fake' user info object to avoid the FB call)
            user = datastructs.UserInfo(userId, None, None, None, None, None, None, None)
            token = datastructs.TokenInfo(tok, userId, int(appId), datetime.datetime.now())
            token = facebook.extendTokenFb(userId, token, int(appId)) or token
            conn = database.getConn()
            curs = conn.cursor()
            try:
                # zzz feels hokey since updateTokensDb() needs as cursor object,
                #     but I also don't want to do an updateDb() call since I don't
                #     have real user info or edges...
                database.updateTokensDb(curs, [user], token)
                conn.commit
            except:
                conn.rollback()
                raise
        else:
            logger.error("Trying to write an authorization for fbid %s with token %s for non-existent client", userId, tok)

    if (eventType == 'shared'):
        # If this was a share, write these friends to the exclusions table so we don't show them for the same content/campaign again
        database.writeFaceExclusionsDb(userId, campaignId, contentId, friends, 'shared', background=config.database.use_threads)

    errorMsg = flask.request.json.get('errorMsg')
    if (errorMsg):
        # may want to push these to the DB at some point, but at least for now,
        # dump them to the logs to ensure we keep the data.
        logger.error('Front-end error encountered for user %s in session %s: %s', userId, sessionId, errorMsg)

    shareMsg = flask.request.json.get('shareMsg')
    if (shareMsg):
        database.writeShareMsgDb(actionId, userId, campaignId, contentId, shareMsg, background=config.database.use_threads)

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
