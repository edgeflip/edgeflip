import logging
import time
from optparse import make_option
from datetime import datetime

from django.core.management.base import NoArgsCommand
from django.utils.daemonize import become_daemon

from targetshare.models import dynamo
from feed_crawler import tasks


logger = logging.getLogger(__name__)

WORKDIR = '/home/mrogers/'
UMASK = 0
PID_FILE = 'daemon_command.pid'
LOGFILE = 'daemon_command.log'
STDOUT = '/dev/null'
STDERR = STDOUT


class Command(NoArgsCommand):
    help = "Starts the crawler service"
    option_list = NoArgsCommand.option_list + (
        make_option(
            '-s', '--sleep',
            help='Number of seconds between loops over the Token table [1800]',
            dest='sleep',
            default=1800
        ),
        make_option(
            '-w', '--workdir',
            action='store', dest='workdir', default=WORKDIR,
            help='Full path of the working directory to which the process should '
            'change on daemon start.'
        ),
        make_option(
            '-u', '--umask',
            action='store', dest='umask', default=UMASK, type="int",
            help='File access creation mask ("umask") to set for the process on '
            'daemon start.'
        ),
        make_option(
            '-p', '--pidfile',
            action='store', dest='pid_file',
            default=PID_FILE, help='PID filename.'
        ),
        make_option(
            '-l', '--logfile', action='store', dest='log_file',
            default=LOGFILE, help='Path to log file'
        ),
        make_option(
            '--daemon-stdout', action='store', dest='daemon_stdout', default=STDOUT,
            help='Destination to redirect standard out'
        ),
        make_option(
            '--daemon-stderr', action='store', dest='daemon_stderr', default=STDERR,
            help='Destination to redirect standard error'
        ),
    )

    def handle_noargs(
        self, sleep, workdir, umask, pid_file, log_file,
        daemon_stdout, daemon_stderr, **options
    ):
        become_daemon(
            our_home_dir=workdir, out_log=daemon_stdout,
            err_log=daemon_stderr, umask=umask
        )
        self.crawl(sleep)

    def crawl(self, sleep):
        logger.info('Starting crawl of all tokens')
        for token in dynamo.Token.items.scan(expires__gt=datetime.now()):
            tasks.crawl_user(token)
        logger.info('Crawl passed, sleeping for {} seconds'.format(sleep))
        time.sleep(sleep)
        self.crawl(sleep)
