"""Settings for the edgeflip project

Configuration
=============

Configuration via conf.d
------------------------

The `edgeflip` project is primarily configured from `YAML <http://en.wikipedia.org/wiki/YAML#Examples>`__
files, whose names end in `.conf`, residing in `conf.d/` directories. These are
loaded into this module in sorted order, and so filenames are usually prefixed
with a 2-digit number to control loading order::

    00-base.conf     10-database.conf  20-stream.conf
    05-logging.conf  10-queue.conf     40-facebook.conf

Base configuration is batteries-included in this package's `conf.d` directory.
Installation- or environment-specific configuration is read from
`/var/www/edgeflip/conf.d` or, if set, a `conf.d/` under the path specified by
environment variable `EDGEFLIP_CONF_DIR`. This additional configuration is
merged *on top* of the base configuration.

Conventions
~~~~~~~~~~~

By convention, each module should get its own configuration file and section.
Try to avoid cluttering up the top level namespace. For example,
(in `60-crawler.conf`)::

    ---
    crawler:
        retries: 42
        proxy: http://example.com

instead of::

    ---
    crawler_retries: 42
    crawler_proxy: http://example.com

Each module should document what options it takes, and provide defaults in
this package's `conf.d/`.

Configuration in Python
-----------------------

Settings may also be applied directly to this file, such that they are
overridden by or override any values set in `conf.d/` directories. Values set
here have the advantage of being able to depend upon or compose configuration
in YAML. However, for simplicity and flexibility, this should generally be
limited to those settings which are not secrets, which are Django-specific
and for which there is no need to vary by environment.

Last-ditch overrides
--------------------

Because configuration may be specified in Python, and to allow for override of
Django settings as yet untouched by a `conf.d/`, `overrides.conf` files, which
reside next to `conf.d/` directories, are loaded at the very end. This YAML
file is intended for emergency and development-time tweaks, without touching
the Python. Generally, and as a rule, `overrides.conf` files should be empty.

Use
===

Generally, this module should not be imported directly. Rather, a settings
object, based on the contents of this file (and Django's defaults), is
available at `django.conf.settings`. For example::

    from django.conf import settings
    settings.DATABASES

It is possible to import this module directly, and thereby have access to
`edgeflip` settings without loading the Django framework; however, this is
discouraged, as it cannot be ensured that these settings will be identical to
those seen otherwise.

"""
import json
import os

import djcelery
import pymlconf
import sh
from kombu import Queue


djcelery.setup_loader()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)


# Determine release #
try:
    # Check for app info JSON file shipped with release artifact:
    app_info = json.load(open(os.path.join(REPO_ROOT, 'app_info.json')))
    RELEASE_VERSION = app_info['version']
except (IOError, ValueError, TypeError, KeyError):
    # App info file missing or malformed.
    # Fall back to git repo revision (for dev):
    git_repo = sh.git.bake(git_dir=os.path.join(REPO_ROOT, '.git'))
    try:
        RELEASE_VERSION = git_repo.describe().strip()
    except Exception:
        # Nothing to fall back on. Go with default:
        RELEASE_VERSION = '0.0'


# Load configuration from conf.d directories #
# default configuration in repo:
config = pymlconf.ConfigManager(dirs=[os.path.join(PROJECT_ROOT, 'conf.d')],
                                filename_as_namespace=False)
# TODO: Configuration shouldn't live with releases; instead: /etc/edgeflip/ ?
env_conf_dir = os.path.expanduser(os.getenv('EDGEFLIP_CONF_DIR',
                                            '/var/www/edgeflip'))
if os.getenv('EDGEFLIP_CONF_DIR') or os.path.isdir('/var/www/edgeflip'):
    # environmental or personal configuration overwrites:
    config.load_dirs([os.path.join(env_conf_dir, 'conf.d')],
                     filename_as_namespace=False)
locals().update((key.upper(), value) for key, value in config.items())


# Django settings #

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'zgoi_vwcwps&13gu&=*zpm-alto_g(bapb31rob(onr(gmg1c_'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'targetshare.middleware.VisitorMiddleware',
    'targetshare.middleware.CookieVerificationMiddleware',
)

ROOT_URLCONF = 'edgeflip.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'edgeflip.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # 3rd-party apps:
    'south',
    'djcelery',
    'django_nose',
    # Edgeflip apps:
    'targetshare',
    'targetadmin',
    'targetmock',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # Default Processors
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    # Edgeflip Processors
    'targetshare.context_processors.context_settings',
)


# Celery settings #
QUEUE_ARGS = {'x-ha-policy': 'all'}
BROKER_URL = 'amqp://{user}:{pass}@{host}:5672/{vhost}'.format(**RABBITMQ)
BROKER_HEARTBEAT = 10
BROKER_POOL_LIMIT = 0 # ELB makes pooling problematic
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_TASK_RESULT_EXPIRES = 3600
CELERY_RESULT_BACKEND = 'database'
CELERY_RESULT_DBURI = "mysql://{USER}:{PASSWORD}@{host}/{NAME}".format(
    host=(DATABASES.default.HOST or 'localhost'),
    **DATABASES.default
)
# FIXME: Short lived sessions won't be needed once we have more consistent
# traffic levels. Then MySQL won't kill our connections.
CELERY_RESULT_DB_SHORT_LIVED_SESSIONS = True
CELERY_QUEUES = (
    Queue('px3', routing_key='px3.crawl', queue_arguments=QUEUE_ARGS),
    Queue('px3_filter', routing_key='px3.filter', queue_arguments=QUEUE_ARGS),
    Queue('px4', routing_key='px4.crawl', queue_arguments=QUEUE_ARGS),
    Queue('bulk_create', routing_key='bulk.create', queue_arguments=QUEUE_ARGS),
    Queue('partial_save', routing_key='partial.save', queue_arguments=QUEUE_ARGS),
    Queue('delayed_save', routing_key='delayed.save', queue_arguments=QUEUE_ARGS),
    Queue('upsert', routing_key='upsert', queue_arguments=QUEUE_ARGS),
    Queue('update_edges', routing_key='update.edges', queue_arguments=QUEUE_ARGS),
)
CELERY_ROUTES = {
    'targetshare.tasks.ranking.px3_crawl': {
        'queue': 'px3',
        'routing_key': 'px3.crawl'
    },
    'targetshare.tasks.ranking.perform_filtering': {
        'queue': 'px3_filter',
        'routing_key': 'px3.filter'
    },
    'targetshare.tasks.ranking.px4_crawl': {
        'queue': 'px4',
        'routing_key': 'px4.crawl'
    },
    'targetshare.tasks.ranking.refine_ranking': {
        # TODO
    },
    'targetshare.tasks.db.bulk_create': {
        'queue': 'bulk_create',
        'routing_key': 'bulk.create'
    },
    'targetshare.tasks.db.partial_save': {
        'queue': 'partial_save',
        'routing_key': 'partial.save'
    },
    'targetshare.tasks.db.delayed_save': {
        'queue': 'delayed_save',
        'routing_key': 'delayed.save'
    },
    'targetshare.tasks.db.upsert': {
        'queue': 'upsert',
        'routing_key': 'upsert',
    },
    'targetshare.tasks.db.update_edges': {
        'queue': 'update_edges',
        'routing_key': 'update.edges',
    },
}
CELERY_IMPORTS = (
    'targetshare.tasks.ranking',
    'targetshare.tasks.db',
)

# Session Settings
SESSION_COOKIE_AGE = 900 # 15 minutes
SESSION_COOKIE_DOMAIN = '.edgeflip.com'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# targetshare settings #
CLIENT_FBOBJECT = {
    'retrieval_cache_timeout': (3600 * 23), # 23 hours
    'campaign_max_age': (3600 * 24), # 24 hours
}
FB_PERMS_LIST = [
    'read_stream', 'user_photos', 'friends_photos',
    'email', 'user_birthday', 'friends_birthday',
    'publish_actions', 'user_about_me', 'user_location',
    'friends_location', 'user_likes', 'friends_likes',
    'user_interests', 'friends_interests'
]
FB_PERMS = ','.join(FB_PERMS_LIST)
MAX_FALLBACK_COUNT = 5
TEST_MODE_SECRET = 'sunwahduck'
VISITOR_COOKIE_NAME = 'visitorid'
VISITOR_COOKIE_DOMAIN = SESSION_COOKIE_DOMAIN

# Test settings #
SOUTH_TESTS_MIGRATE = False
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = (
    '--with-blockage',
    '--with-progressive',
    '--cover-branches',
    '--cover-erase',
    '--cover-html',
    '--cover-package=targetshare',
    '--exclude=^fab$',
    '--http-whitelist=localhost:4444',
    '--logging-level=ERROR',
    '--logging-clear-handlers',
)


# Load override settings #
overrides = pymlconf.ConfigManager(files=[
    # Repo overrides file shouldn't have anything (committed), but check
    # it for dev-time tweaks (and to mirror environment conf directory):
    os.path.join(PROJECT_ROOT, 'overrides.conf'),
])
# Check for (temporary) overrides to above settings in this environment:
overrides_path = os.path.join(env_conf_dir, 'overrides.conf')
if os.path.exists(overrides_path):
    overrides.load_files(overrides_path)
locals().update((key.upper(), value) for key, value in overrides.items())
