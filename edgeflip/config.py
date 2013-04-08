#!/usr/bin/python
import json
import logging
import logging.handlers
import datetime
import os




DEFAULTS_LOCAL_PATH = './edgeflip.config'

defaults = {
    'outdir': '.',
    'codedir': '.',
    'queue': 'edgeflip_demo',
    'logpath': '/tmp/edgeflip-demo.log',
    #'dbpath': './demo.sqlite',
    'dbhost': 'edgeflipdev.cwvoczji8mgi.us-east-1.rds.amazonaws.com',
    'dbuser': 'edgeflip',
    'dbpass': 'B0redsickdog',
    'dbname': 'edgeflipdev',
    #'dburi': 'mysql://edgeflip:B0redsickdog@edgeflipdev.cwvoczji8mgi.us-east-1.rds.amazonaws.com:3306/edgeflipdev'

    # parameters for initial incoming stream reading ("px4")
    'stream_days_in': 120,
    'stream_days_chunk_in': 2,
    'stream_threadcount_in': 60,
    'stream_read_timeout_in': 10,  # seconds
    'stream_read_sleep_in': 0.1,  # seconds

    # parameters for outgoing stream reading ("px5")
    'stream_days_out': 120,
    'stream_days_chunk_out': 10,
    'stream_threadcount_out': 12,
    'stream_read_timeout_out': 20,  # seconds
    'stream_read_sleep_out': 0.2,  # seconds

    # general parameters for crawling and results
    'stream_read_trycount': 3,  # ...strikes and you're out
    'bad_chunk_thresh': 0.25,  # abort crawl if too many chunks fail
    'freshness': 1,

    # FB app parameters
    'fb_app_name': 'edgeflip',
    'fb_app_id': 471727162864364,
    'fb_app_secret': '120fe5e6d5bffa6a9aa3bf075bd3076a',

    # OFA config file locations
    'ofa_state_config': './config/ofa_states.json',
    'ofa_campaign_config': './config/ofa_campaigns.json',
    'ofa_button_redirect': '/ofa_share'

}

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


