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

Note you must import settings *before* modules that are configured by it (currently logging & statsd).

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

Statsd
------

This module will set up `statsd <https://github.com/jsocol/pystatsd>`__.

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
import sh

# base configuration - source tree only
CURRENT_PATH = os.path.dirname(__file__)
REPO_ROOT = os.path.join(CURRENT_PATH, '../')
DEFAULT_CONF_DIR = os.path.join(CURRENT_PATH, 'conf.d')

# system install location
SYSTEM_CONV_DIR = '/var/www/edgeflip/conf.d'

# set in envvar, overrides system
ENV_CONF_DIR = os.path.abspath(os.path.expanduser(os.getenv('EDGEFLIP_CONF_DIR', SYSTEM_CONV_DIR)))

# make a config object, for external use
config = pymlconf.ConfigManager(dirs=[DEFAULT_CONF_DIR], filename_as_namespace=False)

# load environment
config.load_dirs([ENV_CONF_DIR], filename_as_namespace=False)

try:
    git_repo = sh.git.bake(git_dir=os.path.join(REPO_ROOT, '.git'))
    config.app_version = git_repo.describe().strip()
except:
    # This exception comes when celery starts up outside of the app's repo.
    # Catching that exception and setting a dummy value. Celery doesn't need
    # to know the version number
    config.app_version = '0.1'

# set up singletons

logging.config.dictConfig(config.logging)
logger = logging.getLogger(__name__)

logger.info("Configured with %r", config.list_dirs())

# statsd
import statsd
assert statsd.statsd is None
statsd.statsd = statsd.StatsClient(config.statsd.host,
                                   config.statsd.port,
                                   config.statsd.prefix)
