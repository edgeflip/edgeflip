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


def _subprocess(*args, **kws):
    # Use Popen to avoid KeyboardInterrupt messiness
    process = subprocess.Popen(*args, **kws)
    while process.returncode is None:
        try:
            process.poll()
        except KeyboardInterrupt:
            # Pass ctrl+c to the shell
            pass


@fab.task(name='shell')
def start_shell():
    """Open a Django shell"""
    _subprocess(['python', 'manage.py', 'shell'], cwd=BASEDIR)


@fab.task
def ishell():
    """Open a Django shell requiring iPython, with common libraries loaded."""
    commands = [
        "from targetshare import models",
        "from targetshare.integration import facebook",
    ]
    _subprocess(['ipython', '-i', '-c', '; '.join(commands)], cwd=BASEDIR)
