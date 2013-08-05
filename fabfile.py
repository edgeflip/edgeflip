"""Fabric tasks for the edgeflip project

Explore the project's Fabric interface, e.g.:

    $ fab -l
    $ fab -d build
    $ fab -d build.virtualenv

Requires provisioning of Fabric >= 1.6.

"""
from fabric import api as fab

from fab import build, manage, serve, test


@fab.task(name='shell')
def start_shell():
    ''' Drops user into a Django shell '''
    manage('shell')
