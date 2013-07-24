import os.path
from os.path import join

from fabric import api as fab


BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def workon(env):
    """Context manager which sets the PATH to that of the named virtualenv

    Note that an empty argument (e.g. '') returns a functional context
    manager, but the PATH will be functionally unchanged.

    """
    # In the future we might want to support more via the actual "workon"
    # command, (using "fabric.api.prefix"), but that appears to require also
    # prefixing "source /../virtualenvwrapper" (to make that command
    # available). Prepending to the PATH, though it requires knowledge of the
    # env's full path, is much lighter weight.
    path = join('$HOME', '.virtualenvs', env, 'bin') if env else ''
    return fab.path(path, behavior='prepend')
