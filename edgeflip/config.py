#!/usr/bin/python
import json
import logging
import logging.handlers
import datetime
import os

import pymlconf

DEFAULT_CONF_DIR = os.path.join(os.path.dirname(__file__), 'conf.d')

defaults = pymlconf.ConfigManager(dirs=[DEFAULT_CONF_DIR], filename_as_namespace=False)

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
    configFromFile = readJson(infilePath)
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

def readJson(infilePath):
    try:
        return json.load(open(infilePath, 'r'))
    except IOError:
        if (not logging.getLogger().handlers):
            # logging hasn't been set up yet, but we want to log failure to read config file
            setLogger(defaults['logpath'])
        logging.error("config file '%s' not found" % (infilePath))
        return {}

# n.b.: this is not safe against multi-user race conditions
def writeJsonDict(fileName, tag_dataNew, overwriteFile=False):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f")
    tag_data = {} if (overwriteFile) else getConfig(fileName, includeDefaults=False)
    for tag, dataNew in tag_dataNew:
        tag_data[tag] = dataNew
    try:
        tempName = fileName + ".tmp" + ts
        with open(tempName, 'w') as tempFile:
            json.dump(tag_data, tempFile)
        os.rename(fileName, fileName + ".old" + ts)
        os.rename(tempName, fileName)
        return True
    except (IOError, OSError) as err:
        logging.error("error writing config file '%s': %s" % (fileName, err.message))
        return False


