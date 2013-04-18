#!/usr/bin/python
import json
import logging
import logging.handlers
import datetime
import os.path

import pymlconf

DEFAULT_CONF_DIR = os.path.join(os.path.dirname(__file__), 'conf.d')
USER_CONF_DIR = os.getenv('EDGEFLIP_CONF_DIR', '/var/www/edgeflip/conf.d')

config = pymlconf.ConfigManager(dirs=[DEFAULT_CONF_DIR], filename_as_namespace=False)

if os.path.exists(USER_CONF_DIR):
    config.load_dirs(USER_CONF_DIR, filename_as_namespace=False)
    
DEFAULTS_LOCAL_PATH = './edgeflip.config'

# set up logging on the root logger
def setLogger(logpath):
    loghand = logging.handlers.TimedRotatingFileHandler(logpath, when='d', interval=1, backupCount=0, encoding=None, delay=False, utc=False)
    logformat = logging.Formatter(fmt='%(asctime)s\t%(levelname)s\t%(process)d\t%(threadName)s\t%(message)s', datefmt=None)
    loghand.setFormatter(logformat)
    logger = logging.getLogger()
    logger.handlers = []
    logger.addHandler(loghand)
    logger.setLevel(logging.DEBUG)

# do this once on load
# zzz Unfortunately, this does break things if this path isn't defined (eg, with Apache)
#       (But commenting this out means we'll never set the logger if we're using defaults,
#        so obviously we need a better solution longer-term)
# setLogger(defaults['logpath'])

def getDefaults():
    config = dict(defaults)
    return config

def getConfig(infilePath=DEFAULTS_LOCAL_PATH, includeDefaults=False):
    configFromFile = json.load(open(infilePath, 'r'))
    # if we got a new logpath from this read, set the logger
    if ('logpath' in configFromFile):
        setLogger(configFromFile['logpath'])
    elif (includeDefaults):
        # we don't have a logpath in the config file, but are including the default one...
        setLogger(defaults['logpath'])
    config = getDefaults() if (includeDefaults) else {}
    for k, v in config.items():
        logging.debug("config default %s: %s" % (k, str(v)))
    for k, v in configFromFile.items():
        logging.debug("config json %s: %s" % (k, str(v)))
    config.update(configFromFile)
    return config

def writeJsonDict(fileName, tag_dataNew, overwriteFile=False):
    raise NotImplementedError

