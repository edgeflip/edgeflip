"""Fabric tasks to prepare and build the project and its environment"""
from os.path import join

from fabric import api as fab

from . import BASEDIR, manage, true, workon


ENV_NAME = 'edgeflip'

# Break convention for simplicity here:
l = fab.local


# Tasks #

@fab.task(name='all', default=True)
def build_all(deps='1', env=None):
    """Execute all tasks to build the project and its environment

    By default, OS-level dependencies are installed (via task "dependencies").
    This step may be excluded, on platforms which don't require this or which
    don't provide APT, by supplying argument "deps":

        build:deps=[false|0|no|n]

    Otherwise, the following tasks are executed:

        virtualenv
        update-distribute
        requirements
        db

    Customize the virtualenv name by specifying argument "env":

        build:env=MY-ENV

    """
    # dependencies
    if true(deps):
        fab.execute(install_deps)

    # virtualenv
    fab.execute(make_virtualenv, name=env)

    # update-distribute
    # (Needed as long as Ubuntu provides such an old version):
    fab.execute(update_distribute)

    # requirements
    fab.execute(install_reqs)

    # db
    fab.execute(setup_db)

    # static files
    collect_static(True)


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
def setup_db(env=None, force='0', testdata='1'):
    """Initialize the database

    Requires that a virtual environment has been created, and is either
    already activated, or specified, e.g.:

        db:MY-ENV

    To force initialization during development, by tearing down any existing
    database, specify "force":

        db:force=[1|true|yes|y]

    In development, a test data fixture is loaded into the database by default; disable
    this by specifying "testdata":

        db:testdata=[0|false|no|n]

    """
    roles = fab.env.roles or ['dev']
    sql_path = join(BASEDIR, 'edgeflip', 'sql')
    sql_context = {'DATABASE': 'edgeflip', 'USER': 'root'}
    password = None

    # Database teardown
    if 'dev' in roles:
        password = fab.prompt("Enter mysql password:")
        if true(force):
            teardown_sql = open(join(sql_path, 'teardown.sql')).read()
            l('mysql --user=root --password={} --execute="{}"'.format(
                password,
                teardown_sql.format(**sql_context),
            ))
    elif true(force):
        fab.warn("Cannot force database set-up outside of development role {!r}"
                 .format(fab.env.roles))
        return

    # Database initialization
    setup_sql = open(join(sql_path, 'setup.sql')).read()
    setup_prepped = setup_sql.format(**sql_context)
    if password is None:
        l('mysql --user=root -p --execute="{}"'.format(setup_prepped))
    else:
        l('mysql --user=root --password={} --execute="{}"'.format(
            password,
            setup_prepped,
        ))

    # Application schema initialization
    manage('syncdb', flags=['migrate'], env=env)

    # Load test data (dev):
    if 'dev' in roles and true(testdata):
        manage('loaddata', ['test_data'], env=env)


@fab.task
def collect_static(noinput=False, clear=False):
    ''' Collects static files from installed apps to static file path.

    By default this will prompt for input, unless you pass True to the command
    in which case it'll automatically overwrite your current static files with
    a fresh pull:

        collect_static:True

    '''
    flags = []
    if true(noinput):
        flags.append('noinput')
    if true(clear):
        flags.append('clear')
    manage('collectstatic', flags=flags)


# Helpers #
def which_binary(name):
    """Check for path to binary at `name`, with "which"."""
    with fab.settings(warn_only=True): # Handle abortion manually
        return l('which {}'.format(name), capture=True)
