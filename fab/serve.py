"""Fabric tasks for managing servers"""
from fabric import api as fab

from . import manage


# Break convention for simplicity here:
l = fab.local

CELERY_QUEUES = (
    'px3',
    'px4',
    'oauth_token',
    'extend_token',
    'celery',
    'delayed_save',
    'get_or_create',
    'partial_save',
    'bulk_create',
    'upsert',
    'update_edges',
    'user_feeds',
    'initial_crawl',
    'page_likes',
    'back_fill_crawl',
    'incremental_crawl',
    'crawl_comments_and_likes',
    'bg_px4',
    'bg_upsert',
    'bg_update_edges',
    'bg_partial_save',
    'bg_bulk_create',
)


# TODO: Make runserver and celery tasks more like dynamo, s.t. can also do this:
#@fab.task(name='all')
#def start_all():
#    """Start all edgeflip servers
#
#    Namely:
#
#        web (Django)
#        background tasks (Celery)
#        document store (fake dynamo)
#
#    """
#    fab.execute(start_runserver)
#    fab.execute(start_celery)
#    fab.execute(dynamo, command='start')


@fab.task(name='server', default=True)
def start_runserver(host='0.0.0.0', port='8080'):
    """Start the Django runserver with specified host and port"""
    manage('runserver', args=('%s:%s' % (host, port),))


@fab.task(name='celery')
def start_celery(workers='4',
                 loglevel='info',
                 queues=','.join(CELERY_QUEUES)):
    """Start Celery with the specified number of workers and log level

    Directs Celery at the default set of queues, or those specified, e.g.:

        celery:queues="px3\,px3_filter"

    """
    manage('celery', args=('worker',), keyed={
        'concurrency': int(workers),
        'loglevel': loglevel,
        'queues': queues
    })


@fab.task
def dynamo(command='start', *flags, **kws):
    """Manage the dynamo development database server

    This task accepts three commands: "start" [default], "status" and "stop".
    For example:

        dynamo
        dynamo:start
        dynamo:stop

    The first two examples are identical -- they start a mock dynamo database
    server. This server is globally accessible to the system, but by default
    stores its database file and PID record under the working directory's
    repository checkout. The third example stops a server managed by this
    checkout.

    Optional parameters match those of faraday's "local" command.

    """
    commands = ('start', 'stop', 'status')
    if command not in commands:
        fab.abort("Unexpected command, select from: {}".format(', '.join(commands)))

    manage('faraday', ('local', command), flags, kws)
