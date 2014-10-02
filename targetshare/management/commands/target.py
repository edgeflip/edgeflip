import itertools
import json
import os
import sys
import time
import tempfile
from contextlib import closing
from datetime import timedelta
from optparse import make_option
from Queue import Queue
from textwrap import dedent
from threading import Thread

import celery
from django.core.management.base import CommandError, BaseCommand
from django.db import connection
from django.utils import timezone

from targetshare.integration import facebook
from targetshare.models import dynamo, relational
from targetshare.tasks import targeting


def _do_debug(queue, results):
    """Thread worker that debugs enqueued tokens with Facebook and appends validated
    tokens to the results list.

    """
    while True:
        token = queue.get()

        if token is None:
            # Term sentinel; we're done.
            break

        result = facebook.client.debug_token(token.appid, token.token)
        data = result['data']
        if data['is_valid'] and data['expires_at'] > time.time():
            results.append(token)

        queue.task_done()


def debug_tokens(tokens, max_threads, look_ahead=0):
    """Filter a given iterable of Tokens by validity via concurrent requests to
    the Facebook API.

    Valid, unexpired Tokens are passed through.

    """
    queue = Queue(maxsize=(max_threads + look_ahead))
    results = []
    iterator = iter(tokens)

    if max_threads < 1:
        raise ValueError("max_threads must be >= 1")

    # Seed queue and initialize threads
    thread_count = 0
    initial_tokens = itertools.islice(iterator, max_threads)
    for (thread_count, token) in enumerate(initial_tokens, 1):
        queue.put(token)
        thread = Thread(target=_do_debug, args=(queue, results))
        thread.setDaemon(True)
        thread.start()

    # Pad queue according to look_ahead
    for token in itertools.islice(iterator, look_ahead):
        queue.put(token)

    # Feed remaining tokens to queue and share results as they're returned
    for token in iterator:
        # maxsize will block until a slot opens up
        queue.put(token)

        # Share results
        while results:
            yield results.pop()

    queue.join() # let them finish

    for _thread_num in xrange(thread_count):
        queue.put(None) # retire workers

    # Share any remaining results
    for result in results:
        yield result


class ResultView(object):
    """Command extension whose methods generate writeable lines for a given
    iterable of results.

    """
    def __init__(self, command):
        self.command = command

    def shown_faces(self, results):
        """Map each result to a JSON object

            {PRIMARY: [{SECONDARY0: {TOPIC0: SCORE0, ...}}, ...]}

        """
        num_faces = self.command.options['num_faces']
        for result in results:
            if result.ranked:
                primary = result.ranked.primary
                if result.filtered is None:
                    faces = ()
                else:
                    faces = result.filtered.secondaries
                friend_interests = [{str(face.fbid): face.topics} for face in faces[:num_faces]]
                yield json.dumps({str(primary.fbid): friend_interests})
            else:
                yield 'null'

VIEWS = tuple(name for name in vars(ResultView) if not name.startswith('_'))


def get_isolation_level():
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT variable_value "
            "FROM information_schema.session_variables "
            "WHERE variable_name = 'tx_isolation'"
        )
        (isolation_level,) = cursor.fetchone()
    return isolation_level


def set_isolation_level(value):
    with closing(connection.cursor()) as cursor:
        cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL {}'.format(value))


class Command(BaseCommand):

    args = '[PATH]'
    help = dedent("""\
        Target the networks of authorized users via the specified campaign and client content (the
        first and second arguments respectively).

        Authorization tokens are read from the database in arbitrary order, by default;
        alternatively, a list of authorized users may be specified by Facebook ID (FBID), via an
        input file at PATH, or via STDIN (with the argument -).

            python manage.py target 150 150
            python manage.py target 150 150 --limit=50
            python manage.py target 150 150 ./fbids.in
            echo 2904423 | python manage.py target 150 150 -

        """).strip()

    option_list = BaseCommand.option_list + (
        make_option('--limit', type=int,
            help='Number of users to target (if FBIDs not specified)'),
        make_option('--random', action='store_true',
            help='Select tokens randomly (if FBIDs not specified)'),
        make_option('--debug', action='store_true',
            help='Skip tokens that fail a Facebook debugging test'),
        make_option('--display', choices=VIEWS, default='shown_faces', metavar="VIEW",
            help='View of results to display [choices: {}, default: shown_faces]'.format(VIEWS)),
        make_option('--fb-app-id', type=int, metavar="APPID",
            help="A Facebook app ID to which to limit authorizations under consideration"),
        make_option('--num-faces', default=10, type=int, metavar="NUM",
            help="Number of friends' faces to display [default: 10]"),
        make_option('--freshness', default=90, type=int, metavar="DAYS",
            help='Acceptable age of cached network data in days [default: 90]'),
        make_option('--concurrency', default=12, type=int, metavar="NUM",
            help='Number of concurrent targeting tasks to run, (and concurrent '
                 'token debugging threads, if applicable) [default: 12]'),
        make_option('--timeout', default=600, type=int, metavar="SECONDS",
            help='Seconds to wait for a targeting task to be picked up and completed [default: 600]'),
    )

    def __init__(self):
        super(Command, self).__init__()
        self.campaign = None
        self.client_content = None
        self.options = None
        self.verbosity = None

    def pout(self, msg, verbosity=1):
        """Write the given string to stdout as allowed by the verbosity."""
        if self.verbosity >= verbosity:
            self.stdout.write(msg)

    def perr(self, msg, verbosity=1):
        """Write the given string to stderr as allowed by the verbosity."""
        if self.verbosity >= verbosity:
            self.stderr.write(msg)

    def handle(self, campaign_id, client_content_id, fbidfile=None, **options):
        if fbidfile and (options['limit'] or options['random']):
            raise CommandError("FBID input incompatible with options --limit and --random")

        self.campaign = relational.Campaign.objects.get(pk=campaign_id)
        self.client_content = relational.ClientContent.objects.get(pk=client_content_id)

        if self.campaign.client != self.client_content.client:
            raise CommandError("Mismatched campaign and client content")

        self.options = options
        self.verbosity = int(options['verbosity'])

        isolation_level = get_isolation_level()
        if isolation_level != 'READ-COMMITTED':
            self.perr("target not intended for use with {}, "
                      "setting level READ-COMMITTED".format(isolation_level))
            set_isolation_level('READ COMMITTED')

        # Stream tokens thru parallelized background tasks to generate ranked friend networks
        # args => tokens => [debugged tokens] => [sliced tokens] => tasks

        token_stream = self.stream_tokens(fbidfile, options['fb_app_id'])

        if options['debug']:
            token_stream = debug_tokens(token_stream,
                                        max_threads=options['concurrency'],
                                        look_ahead=(options['concurrency'] / 2))

        tokens = itertools.islice(token_stream, options['limit'])
        tasks = self.spawn_tasks(tokens)

        self.pout("targeting networks at proximity rank four with campaign {} "
                  "and client content {}".format(campaign_id, client_content_id))

        # Stream chunked tasks' network results thru chosen view to STDOUT
        # tasks => results => view => STDOUT

        results = self.apply_tasks(tasks,
                                   max_size=options['concurrency'],
                                   timeout=options['timeout'])
        view = getattr(ResultView(self), options['display'])
        for display_line in view(results):
            self.stdout.write(display_line)

    def stream_tokens(self, fbidfile, fb_app_id=None):
        """Generate user tokens."""
        client_app_id = self.campaign.client.fb_app_id

        if fbidfile:
            if fb_app_id and fb_app_id != client_app_id:
                raise CommandError("Facebook app ID is assumed from campaign "
                                   "client when reading FBID stream")
            self.pout("only networks authorized under Facebook app {} will be considered"
                      .format(client_app_id))
            fh = sys.stdin if fbidfile == '-' else open(fbidfile)
            # Grab fbids separated by any space (newline, space, tab):
            fbids = itertools.chain.from_iterable(line.split() for line in fh.xreadlines())
            keys = [{'fbid': int(fbid), 'appid': client_app_id} for fbid in fbids]
            tokens = dynamo.Token.items.batch_get(keys)

        elif self.options['random']:
            fb_app_id = fb_app_id or client_app_id
            self.pout("only networks authorized under Facebook app "
                      "{} will be considered".format(fb_app_id))
            sixty_days_ago = timezone.now() - timedelta(days=60)
            (query, params) = (
                "SELECT DISTINCT user_clients.fbid "
                "FROM user_clients "
                "JOIN clients USING (client_id) "
                "JOIN visitors USING (fbid) "
                "JOIN visits USING (visitor_id) "
                "JOIN events USING (visit_id) "
                "WHERE clients.fb_app_id = %s AND ("
                "   (user_clients.create_dt > %s) OR "
                "   (events.type = 'authorized' AND events.event_datetime > %s)"
                ") ORDER BY RAND()",
                [fb_app_id, sixty_days_ago, sixty_days_ago]
            )

            if self.options['limit']:
                query += " LIMIT %s"
                if self.options['debug']:
                    # Some of these might be no good when debugged, so get 2x
                    params.append(self.options['limit'] * 2)
                else:
                    params.append(self.options['limit'])

            with closing(connection.cursor()) as cursor:
                cursor.execute(query, params)
                fbids = itertools.chain.from_iterable(cursor.fetchall())
                # FIXME: It'd be nice if boto allowed you to specify an
                # (infinite) iterator of keys....
                keys = [{'fbid': fbid, 'appid': fb_app_id} for fbid in fbids]

            tokens = dynamo.Token.items.batch_get(keys)

        else:
            query = dynamo.Token.items.filter(expires__gt=timezone.now())
            if fb_app_id:
                self.pout("only networks authorized under Facebook app "
                          "{} will be considered".format(fb_app_id))
                query = query.filter(appid__eq=fb_app_id)
            tokens = query.scan()

        return tokens.iterable # FIXME

    def spawn_tasks(self, tokens):
        """Generate task signatures from the given stream of tokens."""
        for token in tokens:
            yield targeting.proximity_rank_four.s(
                token,
                campaign_id=self.campaign.pk,
                content_id=self.client_content.pk,
                num_faces=self.options['num_faces'],
                freshness=self.options['freshness'],
                force=True,                         # always perform filtering
                visit_id=targeting.NOVISIT,         # don't record events against any visit
            )

    def apply_tasks(self, tasks, max_size, timeout, wait=0.25):
        """Iteratively submit (chunks of) Celery tasks from the given stream to the
        message queue, and stream their results as they arrive.

        """
        if max_size < 1:
            raise ValueError("max_size must be >= 1")

        iterable = iter(tasks)

        # Let the filesystem manage our pool of task IDs
        # (and make them available to inspection/debugging)
        tmp_dir = tempfile.mkdtemp(prefix='target-')

        while True:
            # Populate / top-off the queue with Celery tasks to monitor
            task_ids = os.listdir(tmp_dir)
            for task in itertools.islice(iterable, (max_size - len(task_ids))):
                async_result = task.apply_async()
                tmp_path = os.path.join(tmp_dir, async_result.id)
                open(tmp_path, 'w').close()

            task_ids = os.listdir(tmp_dir)
            if not task_ids:
                break # no tasks left to monitor

            # Give tasks (and database) a moment
            time.sleep(wait)

            # Check on active tasks
            for task_id in task_ids:
                tmp_path = os.path.join(tmp_dir, task_id)
                async_result = celery.current_app.AsyncResult(task_id)
                if (time.time() - os.path.getmtime(tmp_path)) >= timeout or async_result.ready():
                    # Report completed task result and remove from queue
                    os.remove(tmp_path)

                    if async_result.successful():
                        yield async_result.get()
                    elif async_result.ready():
                        self.perr("Task failed: [{}] {}".format(async_result.id,
                                                                async_result.result))
                    else:
                        self.perr("Task timed out: [{}]".format(async_result.id))

        try:
            os.rmdir(tmp_dir)
        except OSError:
            self.perr("Failed to remove temporary dir {}".format(tmp_dir))
