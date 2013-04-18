#!/usr/bin/python
import logging.config
import os.path
import pymlconf

DEFAULT_CONF_DIR = os.path.join(os.path.dirname(__file__), 'conf.d')
USER_CONF_DIR = os.getenv('EDGEFLIP_CONF_DIR', '/var/www/edgeflip/conf.d')

config = pymlconf.ConfigManager(dirs=[DEFAULT_CONF_DIR], filename_as_namespace=False)

if os.path.exists(USER_CONF_DIR):
    config.load_dirs(USER_CONF_DIR, filename_as_namespace=False)

logging.config.dictConfig(config.logging)