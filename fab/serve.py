"""Fabric tasks for managing servers"""
import os
import signal
from os.path import join

from fabric import api as fab

from . import BASEDIR, manage


# Break convention for simplicity here:
l = fab.local

CELERY_QUEUES = (
    'px3',
    'px3_filter',
    'px4',
    'celery',
    'delayed_save',
    'partial_save',
    'bulk_create',
    'upsert',
    'update_edges',
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
def dynamo(command='start', port='4567', db_path=None, pid_path=None):
    """Manage the dynamo development database server, A.K.A. "fake dynamo"

    This task accepts three commands: "start" [default], "status" and "stop".
    For example:

        dynamo
        dynamo:start
        dynamo:stop

    The first two examples are identical -- they start a fake dynamo database
    server. This server is globally accessible to the system, but by default
    stores its database file and PID record under the working directory's
    repository checkout. The third example stops a server managed by this
    checkout.

    Parameters "db_path" and "pid_path" may be specified to manage fake dynamo
    servers more generally. For example:

        dynamo:db_path=/path/to/db.fdb
        dynamo:stop,pid_path=/path/to/db.pid

    Note that a fake dynamo server invoked with a custom "pid_path" can only
    be shut down by the "stop" command if "pid_path" is specified again.

    """
    commands = ('start', 'stop', 'status')
    if command not in commands:
        fab.abort("Unexpected command, select from: {}"
                  .format(', '.join(commands)))

    default_pid_path = join(BASEDIR, '.fake_dynamo.pid')
    pid_path = pid_path or default_pid_path

    # start #
    if command == 'start':
        l('fake_dynamo -D -d {db_path} -P {pid_path} -p {port}'.format(
            db_path=(db_path or join(BASEDIR, 'fake_dynamo.fdb')),
            pid_path=pid_path,
            port=port,
        ))

    # status #
    if command == 'status':
        try:
            pid = dynamo_pid(pid_path)
        except DynamoNotRunning:
            fab.puts("fake dynamo server status: STOPPED (or none found running)")
        else:
            fab.puts("fake dynamo server status: STARTED ({})".format(pid))

    # stop #
    if command == 'stop':
        try:
            # Retrieve server PID from specified PID file:
            try:
                pid = _dynamo_pid(pid_path)
            except (IOError, ValueError):
                fab.abort("Bad PID file or file path or "
                          "fake dynamo is not running")

            # Kill server:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                fab.abort("fake dynamo server process {} could not be found"
                          .format(pid))
            else:
                # Remove PID file on success:
                os.remove(pid_path)

        finally:
            # Clean up stale PID file, (but only if we own it):
            if os.path.abspath(pid_path) == default_pid_path:
                try:
                    os.remove(default_pid_path)
                except OSError:
                    pass
                else:
                    fab.puts("Stale PID file removed ({})".format(pid_path))


def _dynamo_pid(pid_path):
    return int(open(pid_path).read())


def dynamo_pid(pid_path):
    """Return the process ID of the running fake dynamo server given a path to a
    PID file.

    If no PID or process with that ID is found, raises exception DynamoNotRunning.

    """
    try:
        pid = _dynamo_pid(pid_path)
    except (IOError, ValueError):
        pass
    else:
        try:
            os.kill(pid, 0) # just checks that it's available
        except OSError:
            pass
        else:
            return pid

    raise DynamoNotRunning()


class DynamoNotRunning(Exception):
    pass
