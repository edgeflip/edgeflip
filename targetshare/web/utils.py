"""general web utilities"""

import flask
import hashlib
from Crypto.Cipher import DES
import base64
import urllib
import time
import os
import logging

from ..settings import config

logger = logging.getLogger(__name__)


PADDING = ' '
BLOCK_SIZE = 8

pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE)*PADDING

# DES appears to be limited to 8-character secret, so truncate if too long
secret = pad(config.crypto.des_secret)[:8]
cipher = DES.new(secret)

def encodeDES(message):
    """Encrypt a message with DES cipher, returning a URL-safe, quoted string"""
    message = str(message)
    encrypted = cipher.encrypt(pad(message))
    b64encoded = base64.urlsafe_b64encode(encrypted)
    encoded = urllib.quote(b64encoded)
    return encoded

def decodeDES(encoded):
    """Decrypt a message with DES cipher, assuming a URL-safe, quoted string"""
    encoded = str(encoded)
    unquoted = urllib.unquote(encoded)
    b64decoded = base64.urlsafe_b64decode(unquoted)
    message = cipher.decrypt(b64decoded).rstrip(PADDING)
    return message

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
