"""Fabric tasks to test the project"""
from fabric import api as fab

from . import BASEDIR, workon


DEFAULTS = (
    # ('key', 'value'),
)


# Break convention for simplicity here:
l = fab.local


@fab.task(name='all', default=True)
def test(path='', *args, **kws):
    """Run all, or a subset, of project tests

    To limit test discovery to a particular file or import path, specify the
    "path" argument, e.g.:

        test:targetshare/tests/test_views.py
        test:targetshare.tests.test_views:TestViews.test_best_view

    Positional arguments and both novel and overriding flags may be passed to
    nose, e.g.:

        test:.,pdb,config=my.cfg

    """
    flags = dict(DEFAULTS)
    flags.update(kws)
    with workon():
        with fab.lcd(BASEDIR):
            l('python manage.py test {path} {args} {flags}'.format(
                path=path,
                args=' '.join('--' + arg for arg in args),
                flags=' '.join('--{}={}'.format(key, value)
                            for key, value in flags.items()),
            ))


__test__ = False # In case nose gets greedy
