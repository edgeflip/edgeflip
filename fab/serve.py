import os
import signal
from os.path import join

from fabric import api as fab

from . import BASEDIR


# Break convention for simplicity here:
l = fab.local


@fab.task
def dynamo(command='start', db_path=None, pid_path=None):
    """Manage the dynamo development database server, A.K.A. "fake dynamo"

    This task accepts two commands: "start" [default] and "stop". For example:

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
    commands = ('start', 'stop')
    if command not in commands:
        fab.abort("Unexpected command, select from: {}"
                  .format(', '.join(commands)))

    default_pid_path = join(BASEDIR, '.fake_dynamo.pid')
    pid_path = pid_path or default_pid_path

    if command == 'start':
        l('fake_dynamo -D -d {db_path} -P {pid_path}'.format(
            db_path=(db_path or join(BASEDIR, 'fake_dynamo.fdb')),
            pid_path=pid_path,
        ))

    if command == 'stop':
        try:
            # Retrieve server PID from specified PID file:
            try:
                pid = int(open(pid_path).read())
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
