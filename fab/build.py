"""Fabric tasks to prepare and build the project and its environment"""
import itertools
import os
import os.path
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
    fab.execute(setup_redshift)
    fab.execute(setup_dynamodb)

    # static files
    fab.execute(collect_static, noinput='true')
    fab.execute(install_jsurls, noinput='true')


@fab.task(name='dependencies')
def install_deps():
    """Install OS-level (e.g. C library) dependencies

    Requires that the OS provides APT.

    This task respects the roles under which it is invoked, (and defaults to
    "dev"). "Base" dependencies are always installed, as well as role-specific
    dependencies found in the dependencies/ directory. For example:

        fab -R staging dependencies

    will install dependencies specified by base.dependencies and
    staging.dependencies, given that they are both discovered in the
    dependencies/ directory.

    """
    # Check for apt-get:
    if not which_binary('apt-get'):
        # warn & return rather than abort so as not to raise SystemExit:
        fab.warn("No path to APT, cannot install OS dependencies")
        return

    # Install APT packages specified in dependencies dir:
    roles = fab.env.roles or ['dev'] # Default to just dev
    deps_paths = (join(BASEDIR, 'dependencies', '{}.dependencies'.format(role))
                  for role in itertools.chain(['base'], roles))
    deps = itertools.chain.from_iterable(open(deps_path).readlines()
                                         for deps_path in deps_paths
                                         if os.path.exists(deps_path))
    l('sudo apt-get install -y -q {}'.format(
        ' '.join(dep.strip() for dep in deps)))

    # Install local DynamoDB mock:
    if 'dev' in roles and not os.path.exists(os.path.join(BASEDIR, '.dynamodb')):
        manage('faraday', ('local', 'install'))


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

    This task respects the roles under which it is invoked, (and defaults to
    "dev"). "Base" requirements are always installed, as well as role-specific
    requirements found in the requirements/ directory. For example:

        fab -R staging requirements

    will install requirements specified by base.requirements and
    staging.requirements, given that they are both discovered in the
    requirements/ directory.

    """
    roles = fab.env.roles or ['dev'] # Default to just dev
    reqs_paths = (join('requirements', '{}.requirements'.format(role))
                  for role in itertools.chain(['base'], roles))
    with workon(env):
        with fab.lcd(BASEDIR):
            l('pip install {}'.format(
                ' '.join('-r ' + path for path in reqs_paths
                         if os.path.exists(join(BASEDIR, path)))
            ))


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
        password = os.environ.get('MYSQL_PWD') or fab.prompt("Enter mysql password:")
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
    manage('syncdb', flags=['migrate', 'noinput'], env=env)

    # Load test data (dev):
    if 'dev' in roles and true(testdata):
        manage('loaddata', ['test_data'], env=env)


@fab.task(name='redshift')
def setup_redshift(env=None, force='0', testdata='1'):
    """Initialize a redshift (postgresql) database

    Requires that a virtual environment has been created, and is either
    already activated, or specified, e.g.:

        redshift:MY-ENV

    To force initialization during development, by tearing down any existing
    database, specify "force":

        redshift:force=[1|true|yes|y]

    In development, a test data fixture is loaded into the database by default; disable
    this by specifying "testdata":

        redshift:testdata=[0|false|no|n]

    """
    roles = fab.env.roles or ['dev']
    sql_path = join(BASEDIR, 'reporting', 'sql', 'redshift')
    sql_context = {'DATABASE': 'redshift', 'USER': 'redshift', 'PASSWORD': 'root'}

    # Database teardown
    if 'dev' in roles:
        if true(force):
            teardown_commands = open(join(sql_path, 'teardown.sql')).read().split(';')
            for command in teardown_commands:
                l('sudo -u postgres psql --command="{}"'.format(
                    command.strip().format(**sql_context),
                ))

        # Database initialization
        role_exists = l(
            'sudo -u postgres psql -tAc "select 1 from pg_roles where rolname=\'{USER}\'"'.format(**sql_context),
            capture=True,
        )
        if not role_exists:
            l('sudo -u postgres psql -c "create role {USER} with nosuperuser createdb nocreaterole login password \'{PASSWORD}\';"'.format(**sql_context))

        database_exists = l(
            'sudo -u postgres psql -tAc  "select 1 from pg_database where datname=\'{DATABASE}\'"'.format(**sql_context),
            capture=True
        )
        if not database_exists:
            l('sudo -u postgres psql -c "create database {DATABASE} with '
              'owner={USER} template=template0 encoding=\'utf-8\' '
              'lc_collate=\'en_US.utf8\' lc_ctype=\'en_US.utf8\'"'.format(
                  **sql_context)
              )

        # Application schema initialization
        manage('syncdb', env=env, keyed={
            'database': sql_context['DATABASE'],
        })

        # Load test data:
        if true(testdata):
            manage('loaddata', ['redshift_testdata'], env=env, keyed={
                'database': sql_context['DATABASE'],
            })


@fab.task(name='dynamo')
def setup_dynamodb(env=None, force='0'):
    """Initialize DynamoDB Local database

    Requires that a virtual environment has been created, and is either
    already activated, or specified, e.g.:

        dynamo:MY-ENV

    To force initialization during development, by tearing down any existing
    database, specify "force":

        dynamo:force=[1|true|yes|y]

    """
    if fab.env.roles and 'dev' not in fab.env.roles:
        return # this isn't a dev build

    # Ensure dev server running #
    with fab.settings(fab.hide('running', 'warnings'), warn_only=True):
        status = manage('faraday', ('local', 'status'), env=env, capture=True)

    start_server = status.failed
    if start_server:
        with fab.settings(fab.hide('running', 'stdout')):
            manage('faraday', ('local', 'start'), env=env)

    # Teardown existing database (if forced) #
    if true(force):
        manage('faraday', ['db', 'destroy'], ['force'], env=env)

    # Check for existing database #
    with fab.settings(fab.hide('running')):
        status = manage('faraday', ('db', 'status'), env=env, capture=True)
    if 'ACTIVE' in status:
        fab.warn('DynamoDB tables already exist (specify "force" to overwrite)')
        return # bail

    # Build database #
    manage('faraday', ('db', 'build'), env=env)

    # Stop dev server (if we started it) #
    if start_server:
        with fab.settings(fab.hide('running', 'stdout')):
            manage('faraday', ('local', 'stop'), env=env)


@fab.task
def collect_static(noinput='false', clear='false'):
    """Collects static files from installed apps to project's static file path

    By default this will prompt for input, unless you pass "true" to the command
    in which case it'll automatically overwrite your current static files with
    a fresh pull:

        collect_static:noinput=[1|true|yes|y]

    """
    flags = [key for key, value in locals().items() if true(value)]
    manage('collectstatic', flags=flags)


@fab.task
def install_jsurls(noinput='false', minify='true'):
    flags = [key for key, value in locals().items() if true(value)]
    manage('jsurls', ['install'], flags=flags)


# Helpers #

def which_binary(name):
    """Check for path to binary at `name`, with "which"."""
    with fab.settings(warn_only=True): # Handle abortion manually
        return l('which {}'.format(name), capture=True)
