import csv
import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from targetshare.models import dynamo, relational

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = '<campaign_id> <campaign_id> ...'
    help = ('Command for generating CSV list of FBIDs and email addresses of '
        'users that have shared')
    option_list = BaseCommand.option_list + (
        make_option(
            '-o', '--output',
            help='Name of file to dump CSV contents into',
            dest='output',
            default='sharing_addresses.csv'
        ),
    )

    def handle(self, *args, **options):
        self.campaigns = relational.Campaign.objects.filter(pk__in=args)
        fbids = [{'fbid': x} for x in relational.Event.objects.filter(
            campaign__in=self.campaigns,
            event_type='shared',
        ).values_list('visit__visitor__fbid', flat=True).distinct()]
        if not fbids:
            logger.error('No FBIDs found for campaign')
            return

        self.file_handle = open(options['output'], 'wb')
        writer = csv.writer(self.file_handle)
        writer.writerow(['fbid', 'email'])
        for user in dynamo.User.items.batch_get(keys=fbids):
            writer.writerow([user['fbid'], user['email'].encode('utf8', 'ignore')])

        self.file_handle.close()
