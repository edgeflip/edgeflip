"""Fabric tasks for executing various common commands"""
from fabric import api as fab

from . import manage


@fab.task(name='server', default=True)
def start_runserver(host='0.0.0.0', port='8080'):
    """Start the Django runserver with specified host and port"""
    manage('runserver', args=('%s:%s' % (host, port),))


@fab.task(name='celery')
def start_celery(workers='4',
                 loglevel='info',
                 queues='px3,px3_filter,px4,celery'):
    """Start Celery with the specified number of workers and log level

    Directs Celery at the default set of queues, or those specified, e.g.:

        celery:queues="px3\,px3_filter"

    """
    manage('celery', args=('worker',), keyed={
        'concurrency': int(workers),
        'loglevel': loglevel,
        'queues': queues
    })
