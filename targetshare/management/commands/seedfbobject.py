import sys
import traceback
from itertools import izip
from optparse import make_option
from pprint import pformat
from textwrap import dedent

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import get_text_list

from targetshare.integration import facebook
from targetshare.models import relational


class Command(BaseCommand):

    targets = {'db', 'cache'}

    args = '[{}]'.format('|'.join(targets))
    help = dedent('''\
        Retrieve client FBObjects to populate either only our page cache ("cache") or
        additionally our database ("db").

        cache
        -----

        To specify FBObject pages with which to populate our cache, either stream
        newline-delimited URLs to stdin or use the -u or --url parameter:

            manage.py seedfbobject cache -u http://goofballs.com/1/ -u http://goofballs.com/2/
            manage.py seedfbobject cache --url http://goofballs.com/1/ --url http://goofballs.com/2/
            manage.py seedfbobject cache < goofballurls.txt

        db
        --

        TODO
        ''')

    option_list = BaseCommand.option_list + (
        make_option('-u', '--url',
                    action='append',
                    dest='urls',
                    metavar='URL',
                    help='The URL of an FBObject page'),
    )

    def handle(self, target, **options):
        if target not in self.targets:
            raise CommandError(
                "Specify an appropriate target (one of {})"
                .format(get_text_list(tuple(repr(target) for target in self.targets)))
            )

        try:
            handler = getattr(self, 'handle_' + target)
        except AttributeError:
            raise NotImplementedError(target)
        else:
            handler(**options)

    def handle_cache(self, urls, verbosity, **options):
        verbosity = int(verbosity)

        if urls is None:
            urls = sys.stdin.xreadlines()

        if verbosity >= 2:
            self.stdout.write("Seeding cache with backend `{0.BACKEND}' at `{0.LOCATION}'"
                              .format(settings.CACHES.default), ending="\n\n")

        count = 0
        for count, url in enumerate(urls, 1):
            facebook.third_party.get_fbobject_attributes(url.strip())
            if verbosity >= 3:
                result = cache.get('fbobject|{}'.format(url))
                self.stdout.write(
                    "Added to cache: `{}'\n{}".format(url, pformat(result, indent=4)),
                    ending="\n\n"
                )

        if verbosity >= 2:
            self.stdout.write('Seeded cache with {} URLs'.format(count))

    def handle_db(self, urls, campaigns, **options):
        if (urls and len(urls) > 1) or (campaigns and len(campaigns) > 1):
            raise CommandError(
                "'db' target does not support multiple URLs or "
                "Campaigns from the command line (try stdin)"
            )

        if urls or campaigns:
            if not urls or not campaigns:
                raise CommandError("'db' target requires specification of both "
                                   "a URL and a Campaign")
            data = izip(campaigns, urls)
        else:
            data = (line.strip().split(',') for line in sys.stdin.xreadlines())

        for (campaign_id, url) in data:
            try:
                campaign = relational.Campaign.objects.get(campaign_id=campaign_id)
            except relational.Campaign.DoesNotExist:
                self.stderr.write('TODO!') # TODO
                continue

            try:
                facebook.third_party.source_campaign_fbobject(campaign, url)
            except facebook.third_party.RetrievalError as exc:
                if options['traceback']:
                    self.stderr.write(traceback.format_exc())
                else:
                    self.stderr.write('{}: {}'.format(exc.__class__.__name__, exc))

        # TODO: more stdout?
