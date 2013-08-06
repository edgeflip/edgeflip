"""Package for web-related code, UI & utilities.

.. envvar:: web.app

    A fully-qualified module name indicating the main web app. This module must have an `app` attribute that is the WSGI app to run
"""

from ..settings import config
import logging
import atexit

from statsd import statsd

logger = logging.getLogger(__name__)

_app = None

def getApp():
    """import the primary Flask app as specified by :envvar:`web.app`

    :returns: a Flask app
    """
    global _app
    if _app is None:
        mod = __import__(config.web.app, globals(), {}, 'app')
        _app = getattr(mod, 'app')
        logger.debug("Loaded app from %s", config.web.app)
        statsd.incr(__name__+".startup")
        atexit.register(statsd.incr, __name__+".shutdown")

    return _app
