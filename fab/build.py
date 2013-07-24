"""Fabric tasks to prepare and build the project and its environment"""
from os.path import join

from fabric import api as fab

from . import BASEDIR, workon


ENV_NAME = 'edgeflip'

# Break convention for simplicity here:
l = fab.local


# Tasks #

@fab.task(name='all', default=True)
def build_all(deps='1', env=None, schema=None):
    """Execute all tasks to build the project and its environment

    By default, OS-level dependencies are installed (via task "dependencies").
    This step may be excluded, on platforms which don't require this or which
    don't provide APT, by supplying argument "deps":

        build:deps=[false|0|no|n]

    Otherwise, the following tasks are executed:

        virtualenv
        install
        update-distribute
        requirements
        db

    Customize the virtualenv name by specifying argument "env":

        build:env=MY-ENV

    Or pass a custom DB schema file to task "db" by specifying "schema":

        build:schema=/home/initial.sql

    """
    # dependencies
    if true(deps):
        fab.execute(install_deps)

    # virtualenv
    fab.execute(make_virtualenv, name=env)

    # install
    fab.execute(install_project) # TODO: remove pending Django

    # update-distribute
    # (Needed as long as Flask requires a higher version than Ubuntu provides):
    fab.execute(update_distribute)

    # requirements
    fab.execute(install_reqs)

    # db
    fab.execute(setup_db, schema=schema)


@fab.task(name='dependencies')
def install_deps():
    """Install OS-level (e.g. C library) dependencies

    Requires that the OS provides APT.

    """
    # Check for apt-get:
    if not which_binary('apt-get'):
        # warn & return rather than abort so as not to raise SystemExit:
        fab.warn("No path to APT, cannot install OS dependencies")
        return

    deps_file = join(BASEDIR, 'dependencies.txt')
    deps = open(deps_file).read()
    l('sudo apt-get install -y {}'.format(deps.replace('\n', ' ')))


@fab.task(name='virtualenv')
def make_virtualenv(name=None):
    """Create the project's virtual Python environment

    Requires that OS-level dependencies have been installed.

    By default, the virtualenv is named 'edgeflip'.
    Supply an argument ("name") to change this value:

        virtualenv:MY-ENV

    Returns the environment name (when invoked by another task) and sets this
    value in the Fabric environment.

    """
    name = name or ENV_NAME
    l('''
      source /etc/bash_completion.d/virtualenvwrapper
      mkvirtualenv {}
    '''.format(name), shell='/bin/bash')
    fab.env.virtualenv = name
    return name


@fab.task(name='update-distribute')
def update_distribute(env=None):
    """Update an installation of distibute"""
    with workon(env):
        l('pip install -U distribute')


@fab.task(name='install')
def install_project(env=None):
    """Install the project package into the Python environment (deprecated)

    This task is deprecated, pending migration of Celery to Django.

    Requires that a virtual environment has been created, and is either
    already activated, or specified, e.g.:

        install:MY-ENV

    """
    with workon(env):
        with fab.lcd(BASEDIR): # Allow invokation from anywhere in project
            l('pip install -e .')


@fab.task(name='requirements')
def install_reqs(env=None):
    """Install Python package requirements

    Requires that a virtual environment has been created, and is either
    already activated, or specified, e.g.:

        requirements:MY-ENV

    """
    with workon(env):
        with fab.lcd(BASEDIR):
            l('pip install -r requirements.txt')


@fab.task(name='db')
def setup_db(schema=None, force='0'):
    """Initialize the database

    Optionally specify a custom schema file by supplying an argument ("schema"):

        db:/home/initial.sql

    To force initialization, by tearing down any existing database,
    specify "force":

        db:force=[1|true|yes|y]

    """
    password = fab.prompt("Enter mysql password:")
    if true(force):
        l('mysql --user=root --password={} < {}'.format(
            password,
            join(BASEDIR, 'sql', 'teardown.sql'),
        ))
    l('mysql --user=root --password={} < {}'.format(
        password,
        schema or join(BASEDIR, 'sql', 'initial.sql'),
    ))


# Helpers #

def true(inp):
    """Return whether the given string indicates True."""
    try:
        return inp.lower() in ('true', 'yes', 'y', '1')
    except AttributeError:
        return False


def which_binary(name):
    """Check for path to binary at `name`, with "which"."""
    with fab.settings(warn_only=True): # Handle abortion manually
        return l('which {}'.format(name), capture=True)
