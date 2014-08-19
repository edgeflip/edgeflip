import itertools
import sys
import time
from datetime import timedelta
from optparse import make_option
from Queue import Queue
from textwrap import dedent
from threading import Thread

from celery import group
from django.core.management.base import CommandError, BaseCommand
from django.utils import timezone

from targetshare.integration import facebook
from targetshare.models import dynamo, relational
from targetshare.tasks import targeting


def _do_debug(self, queue, results):
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


def debug_tokens(tokens, max_threads=100):
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


class Command(BaseCommand):

    args = '[PATH]'
    help = dedent("""\
        Target the networks of authorized users via the specified campaign and client content

            python manage.py target 150 150
            python manage.py target 150 150 --limit=50
            python manage.py target 150 150 ./fbids.in
            echo 2904423 | python manage.py target 150 150 -

        """)

    option_list = BaseCommand.option_list + (
        make_option('--limit', type=int, help='Number of users to target (if FBIDs not specified)'),
        make_option('--debug', action='store_true', help='Skip tokens that fail a Facebook debugging test'),
        make_option('--random', action='store_true', help='Select tokens randomly (if FBIDs not specified)'),
    )

    def __init__(self):
        super(Command, self).__init__()
        self.campaign = None
        self.client_content = None
        self.options = None
        self.verbosity = None
        #self.subtasks = None

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

        token_stream = self.stream_tokens(fbidfile)

        if options['debug']:
            token_stream = self.debug_stream(token_stream)

        tokens = itertools.islice(token_stream, options['limit'])

        subtasks = group(self.spawn_subtasks(tokens))
        subtasks.apply_async()

        self.pout("Targeting networks at proximity rank four with campaign {} "
                  "and client content {}".format(campaign_id, client_content_id))
        try:
            for count in itertools.count(1):
                self.pplain("\r")
                self.pplain("." * count)
                written = self.pplain(" [{} tasks completed]".format(subtasks.completed_count()))
                if written:
                    self.stdout.flush()

                if subtasks.ready():
                    self.pout("\n")
                    self.pout(" ...done")
                    break

                time.sleep(1)
        except (Exception, KeyboardInterrupt):
            self.perr("Revoking background tasks ...")
            subtasks.revoke()
            self.perr(" ...done")
            raise

        # TODO: results presentation

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
        debug_size = 500
        if self.options['limit'] and self.options['limit'] < debug_size:
            debug_size = self.options['limit']

        head = ()
        while True:
            batch = itertools.islice(token_stream, debug_size - len(head))
            full_batch = itertools.chain(head, batch)
            for token in debug_tokens(full_batch):
                yield token

            # Force exhausted stream to raise StopIteration for us
            head = (next(token_stream),)

    def spawn_subtasks(self, tokens):
        for token in tokens:
            yield targeting.proximity_rank_four.s(
                token,
                campaign_id=self.campaign.pk,
                content_id=self.client_content.pk,
                num_faces=10,
                force=True,                         # always perform filtering
                freshness=90,                       # 90-day-old cached data is OK
                visit_id=targeting.NOVISIT,         # don't record events against any visit
            )
