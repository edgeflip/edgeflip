import sys
from datetime import timedelta
from itertools import chain
from optparse import make_option
from textwrap import dedent

from django.core.management.base import CommandError, BaseCommand
from django.utils import timezone

from targetshare.models import dynamo, relational
from targetshare.tasks import targeting


class Command(BaseCommand):

    args = '[PATH]'
    help = dedent("""\
        Target the networks of authorized users via the specified campaign

            python manage.py target --campaign=150 --content=150
            python manage.py target --campaign=150 --content=150 --limit=50
            python manage.py target ./fbids.in --campaign=150 --content=150
            echo 2904423 | python manage.py target - --campaign=150 --content=150

        """)

    option_list = BaseCommand.option_list + (
        make_option('--campaign', dest='campaign_id', help='Campaign to query'),
        make_option('--content', dest='client_content_id', help='Client content to query'),
        make_option('--limit', type=int, help='Number of users to target (if fbids not specified)'),
        make_option('--debug', action='store_true', help='Skip tokens that fail a Facebook debugging test'),
        make_option('--random', action='store_true', help='Select tokens randomly'),
    )

    def __init__(self):
        super(Command, self).__init__()
        self.campaign = None
        self.client_content = None
        self.options = None
        self.verbosity = None
        self.task_ids = None

    def handle(self, fbidfile, **options):
        if options['fbidfile'] and (options['limit'] or options['random']):
            raise CommandError("option --fbidfile incompatible with options --limit and --random")

        self.campaign = relational.Campaign.objects.get(pk=options['campaign_id'])
        self.client_content = relational.ClientContent.objects.get(pk=options['client_content_id'])

        if self.campaign.client != self.client_content.client:
            raise CommandError("Mismatched campaign and client content")

        self.options = options
        self.verbosity = int(options['verbosity'])

        self.task_ids = tuple(self.spawn_tasks(self.stream_tokens(fbidfile)))

        # TODO: ...

    def stream_tokens(self, fbidfile):
        fb_app_id = self.campaign.client.fb_app_id

        if fbidfile:
            fh = sys.stdin if fbidfile == '-' else open(fbidfile)
            # Grab fbids separated by any space (newline, space, tab):
            fbids = chain.from_iterable(line.split() for line in fh.xreadlines())
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
                num_fbids = self.options['limit']
            keys = [{'fbid': fbid, 'appid': fb_app_id}
                    for fbid in random_fbids[:num_fbids].iterator()]
            tokens = dynamo.Token.items.batch_get(keys)

        else:
            tokens = dynamo.Token.items.scan(appid__eq=fb_app_id, expires__gt=timezone.now())

        return tokens.iterable # FIXME

    def spawn_tasks(self, tokens):
        for token in tokens:
            # should maybe more lax about freshness?
            # and, don't record a visit
            task = targeting.proximity_rank_four.delay(token, #...
                                                    )
            yield task.id
