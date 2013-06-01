"""general web utilities"""

import flask
import hashlib
import time
import os
import logging

logger = logging.getLogger(__name__)


def ajaxResponse(content, code, sessionId):
    """return a response with custom session ID header set"""
    
    resp = flask.make_response(content, code)
    resp.headers['X-EF-SessionID'] = sessionId
    return resp

def getIP(req):
    """return the client's IP"""
    if not req.headers.getlist("X-Forwarded-For"):
        return req.remote_addr
    else:
        return req.headers.getlist("X-Forwarded-For")[0]

def generateSessionId(ip, content, timestr=None):
    """generate a session id
    
    replace me with browser session cookie w/ short expiry,
    ttl resets on each interaction

    Add a permanent cookie too.
    """
    if (not timestr):
        timestr = '%.10f' % time.time()
    # Is MD5 the right strategy here?
    sessionId = hashlib.md5(ip+content+timestr).hexdigest()
    logger.debug('Generated session id %s for IP %s with content %s at time %s', sessionId, ip, content, timestr)
    return sessionId

def locateTemplate(templateName, clientSubdomain, app):
    fullPath = os.path.join(app.root_path, app.template_folder, 'clients', clientSubdomain, templateName)
    if (os.path.exists(fullPath)):
        return 'clients/%s/%s' % (clientSubdomain, templateName)
    else:
        return templateName
