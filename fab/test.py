"""Fabric tasks to test the project"""
import os.path
import shutil
import tempfile

from fabric import api as fab

from . import manage, serve, true


DEFAULT_FLAGS = (
    'noinput',
)

DEFAULT_KEY_ARGS = (
    # ('key', 'value'),
)


@fab.task(name='all', default=True)
def test(path='', *args, **kws):
    """Run all, or a subset, of project tests

    To limit test discovery to a particular file or import path, specify the
    "path" argument, e.g.:

        test:targetshare/tests/test_views.py
        test:targetshare.tests.test_views:TestViews.test_best_view

    Flags and both novel and overriding keyword arguments may be passed to
    nose, e.g.:

        test:.,pdb,config=my.cfg

    This task sets some flags by default. To clear these, pass the flag or
    keyword argument "clear-defaults":

        test:.,clear-defaults
        test:clear-defaults=[true|yes|y|1]

    """
    # Determine test arguments #
    flags = list(args)

    # Include default flags?
    try:
        flags.remove('clear-defaults')
    except ValueError:
        clear_default_args0 = False
    else:
        clear_default_args0 = True
    clear_default_args1 = true(kws.pop('clear-defaults', None))
    if not clear_default_args0 and not clear_default_args1:
        flags.extend(DEFAULT_FLAGS)

    key_args = dict(DEFAULT_KEY_ARGS)
    key_args.update(kws)

    # Ensure local dynamo is running #
    dynamo_dir = tempfile.mkdtemp()
    pid_path = os.path.join(dynamo_dir, 'pid')
    ddb_args = {'pid-path': pid_path}
    fab.execute(serve.dynamo, 'start', 'memory', port='4444', **ddb_args)

    # Test #
    try:
        manage('test', [path], flags, key_args)
    finally:
        # Terminate local dynamo:
        fab.execute(serve.dynamo, 'stop', **ddb_args)
        shutil.rmtree(dynamo_dir)


__test__ = False # In case nose gets greedy
