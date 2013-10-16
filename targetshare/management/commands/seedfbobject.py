import sys
import traceback
from optparse import make_option
from pprint import pformat
from textwrap import dedent

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import NoArgsCommand, CommandError, OutputWrapper

from targetshare.integration import facebook
from targetshare.models import relational


class Command(NoArgsCommand):

    help = dedent('''\
        Retrieve client FBObjects to populate either only our page cache or
        additionally our database.

        To specify FBObject pages with which to populate our cache, either stream
        newline-delimited URLs to stdin or use the -u or --url parameter:

            manage.py seedfbobject -u http://goofballs.com/1/ -u http://goofballs.com/2/
            manage.py seedfbobject --url http://goofballs.com/1/ --url http://goofballs.com/2/
            manage.py seedfbobject < goofballurls.txt

        Additionally, the database may be populated by specifying a campaign by its primary key:

            manage.py seedfbobject -c 42 -u http://goofballs.com/1/ -u http://goofballs.com/2/
            manage.py seedfbobject < goofballurls.txt

        Stdin lines may consist of either a URL or a URL paired with a campaign primary key:

            http://goofballs.com/1/
            http://goofballs.com/2/ 42
            http://goofballs.com/3/ 42
            http://goofballs.com/3/ 43

        ''')

    option_list = NoArgsCommand.option_list + (
        make_option('-c', '--campaign',
                    dest='campaign_id',
                    type=int,
                    help='The primary key of a campaign'),
        make_option('-u', '--url',
                    action='append',
                    dest='urls',
                    metavar='URL',
                    help='The URL of an FBObject page'),
    )

    def report(self, message, level, verbosity, ending=None):
        if verbosity >= level:
            self.stdout.write(message, ending=ending)

    def report_exception(self, exc, **options):
        if options['traceback']:
            self.stderr.write(traceback.format_exc())
        else:
            self.stderr.write('{}: {}'.format(exc.__class__.__name__, exc))

    def handle_noargs(self, campaign_id=None, urls=None, verbosity=1, **options):
        verbosity = int(verbosity) # Comes to us as a str

        # Django is weird about setting up stderr, so ensure it's set:
        self.stderr = getattr(self, 'stderr', OutputWrapper(sys.stderr, self.style.ERROR))

        if campaign_id:
            if not urls:
                raise CommandError("No URLs specified")
            data = ((url, campaign_id) for url in urls)
        elif urls:
            data = ((url,) for url in urls)
        else:
            data = (line.strip().split() for line in sys.stdin.xreadlines())

        self.report("Seeding cache with backend `{0.BACKEND}' at `{0.LOCATION}'"
                    .format(settings.CACHES.default), 2, verbosity, ending="\n\n")

        cache_count, db_count = (0,) * 2
        for line in data:
            try:
                url, campaign_id = line
            except ValueError:
                (url,) = line
                if self.seed_cache(url, verbosity=verbosity, **options):
                    cache_count += 1
            else:
                if self.seed_db(url, campaign_id, verbosity=verbosity, **options):
                    db_count += 1

        self.report('Seeded cache with {} URLs'.format(cache_count),
                    level=2, verbosity=verbosity)
        self.report('Seeded db (and cache) with {} objects'.format(db_count),
                    level=2, verbosity=verbosity)

    def seed_cache(self, url, verbosity, **options):
        try:
            facebook.third_party.get_fbobject_attributes(url, refresh=True)
        except facebook.third_party.RetrievalError as exc:
            self.report_exception(exc, traceback=options['traceback'])
            return False
        else:
            result = cache.get('fbobject|{}'.format(url))
            self.report("Added to cache: `{}'\n{}".format(url, pformat(result, indent=4)),
                        level=3, verbosity=verbosity, ending='\n\n')
            return True

    def seed_db(self, url, campaign_id, verbosity, **options):
        try:
            campaign = relational.Campaign.objects.get(campaign_id=campaign_id)
        except relational.Campaign.DoesNotExist:
            self.stderr.write('Invalid campaign identifier: {!r}'.format(campaign_id))
            return False

        try:
            fb_object = facebook.third_party.source_campaign_fbobject(campaign, url,
                                                                      refresh=True)
        except facebook.third_party.RetrievalError as exc:
            self.report_exception(exc, traceback=options['traceback'])
            return False
        else:
            self.report("FBObject {} sourced under Campaign {}"
                        .format(fb_object.pk, campaign_id),
                        level=3, verbosity=verbosity)
            return True
