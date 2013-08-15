"""Fabric tasks for the edgeflip project

Explore the project's Fabric interface, e.g.:

    $ fab -l
    $ fab -d build
    $ fab -d build.virtualenv

Requires provisioning of Fabric >= 1.6.

"""
import subprocess

from fabric import api as fab

from fab import BASEDIR, build, serve, test


@fab.task(name='shell')
def start_shell():
    """Open a Django shell"""
    # Use Popen to avoid KeyboardInterrupt messiness
    process = subprocess.Popen(['python', 'manage.py', 'shell'], cwd=BASEDIR)
    while process.returncode is None:
        try:
            process.poll()
        except KeyboardInterrupt:
            # Pass ctrl+c to the shell
            pass
