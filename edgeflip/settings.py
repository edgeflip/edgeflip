#!/usr/bin/python
import logging.config
import os.path
import pymlconf

# base configuration - source tree only 
DEFAULT_CONF_DIR = os.path.join(os.path.dirname(__file__), 'conf.d')

# system install location
SYSTEM_CONV_DIR = '/var/www/edgeflip/conf.d'

# set in envvar, overrides system
ENV_CONF_DIR = os.path.abspath(os.path.expanduser(os.getenv('EDGEFLIP_CONF_DIR', SYSTEM_CONV_DIR)))

# make a config object, for external use
config = pymlconf.ConfigManager(dirs=[DEFAULT_CONF_DIR], filename_as_namespace=False)

# load environment
config.load_dirs([ENV_CONF_DIR], filename_as_namespace=False)

# set up singletons

logging.config.dictConfig(config.logging)
logging.info("Configured with %r", config.list_files())



