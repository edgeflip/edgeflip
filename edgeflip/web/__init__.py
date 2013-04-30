from ..settings import config
import logging

logger = logging.getLogger(__name__)

_app = None

def getApp():
    """return the flask app specified by configuration
    
    """
    global _app
    if _app is None:
        mod = __import__(config.web.app, globals(), {}, 'app')
        _app = getattr(mod, 'app')
        logger.debug("Loaded app from %s", config.web.app)
    
    return _app
    