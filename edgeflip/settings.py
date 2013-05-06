#!/usr/bin/python
"""Configuration for Edgeflip app

Using configuration in your code
--------------------------------

Code using configuration should import the `config` object from this module, like so::

    >>> from .settings import config
    >>> for i in config.crawler.retries:
    ...     <do whatever>
    >>> print("Vote for", config.skin["first_name"], config.skin["last_name"])

`config` is a :mod:`pymlconf` dict-object; config items can be accessed as properties or by item lookup.

Configuring the app
-------------------

Configuration uses `conf.d/` style configuration directories. A directory should contain `YAML <http://en.wikipedia.org/wiki/YAML#Examples>`__ files ending in `.conf`. These are loaded in sorted order. Filenames are usually prefixed with a 2-digit number to control loading order::

    00-base.conf     10-database.conf  20-stream.conf
    05-logging.conf  10-queue.conf     40-facebook.conf


Base configuration is batteries-included in this package's `conf.d` directory. It is loaded automatically.

Custom configuration will be read from `/var/www/edgeflip/conf.d`. This is merged *on top* of the base package config. You can override the location of your custom config by setting the `EDGEFLIP_CONF_DIR` environment variable.

Logging
-------

This module will set up stdlib :mod:`logging` using `config.logging`. By default, all log messages go to the console. There is a syslog handler ready for use; just set `logging.root = [syslog]`  somewhere in your custom config instead.

Conventions
-----------
By convention, each module should get its own config section. Try to avoid cluttering up the top level config namespace. So do this (in `60-crawler.conf`)::

    --- 
    crawler:
        retries: 42
        proxy: http://example.com

instead of::

    --- 
    crawler_retries: 42
    crawler_proxy: http://example.com

Each module should document what options it takes, and provide defaults in this package's `conf.d/`
"""
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
logger = logging.getLogger(__name__)

logger.info("Configured with %r", config.list_dirs())

