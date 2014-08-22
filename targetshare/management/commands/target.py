import itertools
import json
import sys
import time
from collections import deque
from datetime import timedelta
from optparse import make_option
from Queue import Queue
from textwrap import dedent
from threading import Thread

from celery import group
from django.core.management.base import CommandError, BaseCommand
from django.db import transaction
from django.utils import timezone

from targetshare.integration import facebook
from targetshare.models import dynamo, relational
from targetshare.tasks import targeting


# Number of tokens to request at once for parallelized debugging
# (see DEBUG_MAX_THREADS)
DEBUG_SIZE = 500

# Maximum number of tokens which will be debugged at once (by separate threads)
DEBUG_MAX_THREADS = 100


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


def debug_tokens(tokens, max_threads=DEBUG_MAX_THREADS):
    """Test a given iterable of Tokens for validity via concurrent requests to
    the Facebook API.

    Valid, unexpired Tokens are returned in a list.

    """
    debugged = []
    queue = Queue()
    thread_count = 0
    iterator = iter(tokens)

    if max_threads < 1:
        raise ValueError("max_threads must be >= 1")

    while thread_count < max_threads:
        try:
            token = next(iterator)
        except StopIteration:
            break
        else:
            queue.put(token)
            thread = Thread(target=_do_debug, args=(queue, debugged))
            thread.setDaemon(True)
            thread.start()
            thread_count += 1
    else:
        for token in iterator:
            queue.put(token)

    queue.join()

    for _count in xrange(thread_count):
        queue.put(None) # relieve debugging threads

    return debugged


def _do_task_group(queue, results):
    """Thread worker that submits enqueued groups of Celery tasks to the message
    queue and reports their results.

    """
    while True:
        subtasks = queue.get()

        if subtasks is None:
            # Term sentinel; we're done.
            break

        grp = group(subtasks)
        async_results = grp.apply_async()
        while async_results.waiting():
            # Commit implicit REPEATABLE READ transaction
            # FIXME: This should've just been one line:
            # FIXME: results.extend(async_results.join())
            transaction.commit_unless_managed()
            time.sleep(0.1)
        results.extend(async_results.get())

        queue.task_done()


def group_subtasks(subtasks, num, size):
    """Iteratively submit (chunks of) Celery tasks from the given stream to the
    message queue and stream their results as they arrive.

    """
    if num < 1:
        raise ValueError("group num must be >= 1")

    queue = Queue()
    results = deque()

    for _thread_num in xrange(num):
        # Start worker
        thread = Thread(target=_do_task_group, args=(queue, results))
        thread.setDaemon(True)
        thread.start()

    while True:
        if queue.unfinished_tasks < num:
            # Share results
            for _result_num in xrange(min(size, len(results))):
                yield results.popleft()

            # Enqueue task group
            task_group = tuple(itertools.islice(subtasks, size))
            if not task_group:
                break # we're already done
            queue.put(task_group)

    queue.join() # let them finish (FIXME: ^C)

    for _thread_num in xrange(num):
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
        make_option('--task-group-size', default=4, type=int, metavar="NUM",
            help='Number of ranking tasks to wait on at a time (this should not be more than '
                 'the number of available Celery workers) [default: 4]'),
        make_option('--task-groups', default=3, type=int, metavar="NUM",
            help='Number of groups of ranking tasks to maintain in parallel [default: 3]'),
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

    def pplain(self, msg, verbosity=1):
        """Write the given string to stdout as allowed by the verbosity.

        No "new line" character is forced onto the end of the string; it is
        printed "plain".

        A Boolean is returned indicating whether the message was allowed by the
        verbosity setting, (which may be used to determine whether to flush
        stdout).

        """
        if self.verbosity >= verbosity:
            self.stdout.write(msg, ending='')
            return True
        return False

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
            token_stream = self.debug_stream(token_stream)

        tokens = itertools.islice(token_stream, options['limit'])
        subtasks = self.spawn_subtasks(tokens)

        self.pout("targeting networks at proximity rank four with campaign {} "
                  "and client content {}".format(campaign_id, client_content_id))

        # Stream chunked tasks' network results thru chosen view to STDOUT
        # grouped tasks => view => STDOUT

        results = group_subtasks(subtasks,
                                 self.options['task_groups'],
                                 self.options['task_group_size'])
        view = getattr(ResultView(self), options['display'])
        for display_line in view(results):
            self.stdout.write(display_line)

    def stream_tokens(self, fbidfile):
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
            tokens = dynamo.Token.items.scan(appid__eq=fb_app_id, expires__gt=timezone.now())

        return tokens.iterable # FIXME

    def debug_stream(self, token_stream):
        debug_size = DEBUG_SIZE
        if self.options['limit'] and self.options['limit'] < debug_size:
            debug_size = self.options['limit']

        head = ()
        while True:
            batch = itertools.islice(token_stream, debug_size - len(head))
            full_batch = itertools.chain(head, batch)
            for token in debug_tokens(full_batch):
                yield token

            # Force exhausted stream to raise StopIteration for us
            # (rather than iterating over empty slices forever)
            head = (next(token_stream),)

    def spawn_subtasks(self, tokens):
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
