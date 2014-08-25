import itertools
import json
import sys
import time
from datetime import timedelta
from optparse import make_option
from Queue import Queue
from textwrap import dedent
from threading import Thread

from django.core.management.base import CommandError, BaseCommand
from django.db import transaction
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
            primary = result.ranked.primary
            faces = result.filtered.secondaries[:num_faces]
            yield json.dumps({
                str(primary.fbid): [{str(face.fbid): face.topics} for face in faces]
            })

VIEWS = tuple(name for name in vars(ResultView) if not name.startswith('_'))


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
        make_option('--num-faces', default=10, type=int, metavar="NUM",
            help="Number of friends' faces to display [default: 10]"),
        make_option('--freshness', default=90, type=int, metavar="DAYS",
            help='Acceptable age of cached network data in days [default: 90]'),
        make_option('--concurrency', default=12, type=int, metavar="NUM",
            help='Number of concurrent targeting tasks to run, (and concurrent '
                 'token debugging threads, if applicable) [default: 12]'),
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

        # Stream tokens thru parallelized background tasks to generate ranked friend networks
        # args => tokens => [debugged tokens] => [sliced tokens] => tasks

        token_stream = self.stream_tokens(fbidfile)

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

        results = self.apply_tasks(tasks, max_size=options['concurrency'])
        view = getattr(ResultView(self), options['display'])
        for display_line in view(results):
            self.stdout.write(display_line)

    def stream_tokens(self, fbidfile):
        """Generate user tokens."""
        fb_app_id = self.campaign.client.fb_app_id

        if fbidfile:
            fh = sys.stdin if fbidfile == '-' else open(fbidfile)
            # Grab fbids separated by any space (newline, space, tab):
            fbids = itertools.chain.from_iterable(line.split() for line in fh.xreadlines())
            keys = [{'fbid': int(fbid), 'appid': fb_app_id} for fbid in fbids]
            tokens = dynamo.Token.items.batch_get(keys)

        elif self.options['random']:
            sixty_days_ago = timezone.now() - timedelta(days=60)
            app_users = relational.UserClient.objects.filter(client___fb_app_id=fb_app_id)
            recently_added_users = app_users.filter(create_dt__gt=sixty_days_ago)
            recently_visited_users = app_users.filter(
                visitor__visits__events__event_type='authorized',
                visitor__visits__events__event_datetime__gt=sixty_days_ago,
            )
            active_users = recently_added_users | recently_visited_users
            random_fbids = active_users.values_list('fbid', flat=True).distinct().order_by('?')
            if self.options['debug'] and self.options['limit']:
                # Some of these might be no good when debugged, so get 2x
                num_fbids = self.options['limit'] * 2
            else:
                # It'd be nice if boto allowed you to specify an (infinite)
                # iterator of keys (this might be None)....
                num_fbids = self.options['limit']
            keys = [{'fbid': fbid, 'appid': fb_app_id}
                    for fbid in random_fbids[:num_fbids].iterator()]
            tokens = dynamo.Token.items.batch_get(keys)

        else:
            query = dynamo.Token.items.filter(appid__eq=fb_app_id, expires__gt=timezone.now())
            tokens = query.scan(limit=self.options['limit'])

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

    def apply_tasks(self, tasks, max_size, wait=0.1):
        """Iteratively submit (chunks of) Celery tasks from the given stream to the
        message queue, and stream their results as they arrive.

        """
        if max_size < 1:
            raise ValueError("max_size must be >= 1")

        queue = []
        iterable = iter(tasks)

        while True:
            # Populate / top-off the queue with Celery tasks to monitor
            for task in itertools.islice(iterable, (max_size - len(queue))):
                async_result = task.apply_async()
                queue.append(async_result)

            if not queue:
                break # no tasks left to monitor

            # Give tasks (and database) a moment
            time.sleep(wait)

            # Check on active tasks
            for async_result in queue:
                if async_result.ready():
                    # Report completed task result and remove from queue
                    queue.remove(async_result)

                    if async_result.successful():
                        yield async_result.get()
                    else:
                        self.perr("Task failed: [{}] {}".format(async_result.id,
                                                                async_result.result))

            # Commit implicit REPEATABLE READ transaction
            transaction.commit_unless_managed()
