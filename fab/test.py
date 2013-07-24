"""Fabric tasks to test the project"""
from fabric import api as fab

from . import BASEDIR, workon


# Break convention for simplicity here:
l = fab.local


@fab.task(name='all', default=True)
def test(*args, **kws):
    """Run all project tests

    Positional arguments and both novel and overriding flags may be passed to
    nose, e.g.:

        test:pdb,config=my.cfg

    """
    flags = {'config': 'nose.cfg'}
    flags.update(kws)
    with workon(fab.env.get('virtualenv')):
        with fab.lcd(BASEDIR):
            l('nosetests edgeflip/tests {args} {flags}'.format(
                args=' '.join('--' + arg for arg in args),
                flags=' '.join('--{}={}'.format(key, value)
                            for key, value in flags.items()),
            ))


__test__ = False # In case nose gets greedy
