""" Fabric tasks for executing various common commands """
from fabric import api as fab

from . import manage


@fab.task(name='celery')
def start_celery(workers=4, loglevel='info', queues=None):
    ''' Fires up celery with the specified number of workers, log level, and
    points it at a default set of queues (or the ones specified)
    '''
    if queues:
        queues = ','.join(queues)
    else:
        queues = 'px3,px3_filter,px4,celery'
    manage('celery', args=('worker',), keyed={
        'concurrency': workers,
        'loglevel': loglevel,
        'queues': queues
    })


@fab.task(name='server')
def start_runserver(host='127.0.0.1', port='8000'):
    ''' Starts up the django runserver with specified host and port '''
    manage('runserver', args=('%s:%s' % (host, port),))
