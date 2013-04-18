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

# set up logging on the root logger
def setLogger(logpath):
    loghand = logging.handlers.TimedRotatingFileHandler(logpath, when='d', interval=1, backupCount=0, encoding=None, delay=False, utc=False)
    logformat = logging.Formatter(fmt='%(asctime)s\t%(levelname)s\t%(process)d\t%(threadName)s\t%(message)s', datefmt=None)
    loghand.setFormatter(logformat)
    logger = logging.getLogger()
    logger.handlers = []
    logger.addHandler(loghand)
    logger.setLevel(logging.DEBUG)

