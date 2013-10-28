import csv
import logging
import hashlib
from decimal import Decimal
from optparse import make_option
from datetime import datetime

from django.core.urlresolvers import reverse
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from targetshare.models import dynamo, relational
from targetshare.tasks import db, ranking
from targetshare.templatetags.string_format import lexical_list

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = '<campaign_id> <content_id>'
    help = 'Command for generating Faces Email CSV'
    option_list = BaseCommand.option_list + (
        make_option(
            '-m', '--mock',
            help='Flag to enable mock mode for FaceBook crawls [False]',
            action='store_true',
            dest='mock',
            default=False
        ),
        make_option(
            '-n', '--num-face',
            help='Number of friends to grab [3]',
            default=3,
            dest='num_face',
            type='int'
        ),
        make_option(
            '-o', '--output',
            help='Name of file to dump CSV contents into',
            dest='output',
        ),
        make_option(
            '-u', '--url',
            help='Overrides default URL builder with given url',
            dest='url'
        ),
        make_option(
            '-c', '--cache',
            help='Use the Civis cache or not [True]',
            action='store_true',
            dest='cache',
            default=True
        ),
    )

    def handle(self, campaign_id, content_id, mock, num_face,
               output, url, cache, **options):
        # DB objects
        self.campaign = relational.Campaign.objects.get(pk=campaign_id)
        self.content = relational.ClientContent.objects.get(pk=content_id)
        self.client = self.campaign.client

        # Settings
        self.mock = mock
        self.num_face = num_face
        self.cache = cache

        if output:
            self.filename = output
        else:
            self.filename = 'faces_email_%s.csv' % datetime.now().strftime(
                '%m-%d-%y_%H:%M:%S')
        self.file_handle = open(self.filename, 'wb')
        self.csv_writer = csv.writer(self.file_handle)
        self.csv_writer.writerow([
            'primary_fbid', 'email', 'friend_fbids', 'names', 'html_table'
        ])

        self.url = url
        self.task_list = {}
        self.edge_collection = {}
        self.notification = relational.Notification.objects.create(
            campaign=self.campaign,
            client_content=self.content
        )
        self.failed_fbids = []

        # Process information
        logger.info('Starting crawl')
        self._crawl_and_filter()
        self.file_handle.close()
        logger.info('Faces Email Complete')

    def _crawl_and_filter(self):
        ''' Grabs all of the tokens for a given UserClient, and throws them
        through the px3 crawl again
        '''
        logger.info('Gathering list of users to crawl')
        user_fbids = [{
            'fbid': Decimal(x),
            'appid': self.client.fb_app_id,
        } for x in self.client.userclients.values_list('fbid', flat=True)]
        user_tokens = dynamo.Token.items.batch_get(keys=user_fbids)
        count = 0
        for ut in user_tokens:
            hash_str = hashlib.md5('{}{}{}{}'.format(
                ut['fbid'], self.campaign.pk,
                self.content.pk, self.notification.pk
            )).hexdigest()
            notification_user, created = relational.NotificationUser.objects.get_or_create(
                uuid=hash_str, fbid=ut['fbid'], notification=self.notification
            )
            try:
                edges = ranking.px3_crawl(
                    mockMode=self.mock,
                    fbid=ut['fbid'],
                    token=ut
                )
            except IOError:
                logger.exception('Failed to crawl {}'.format(ut['fbid']))
                self.failed_fbids.append(ut['fbid'])
                continue

            try:
                self.edge_collection[notification_user.uuid] = ranking.perform_filtering(
                    edgesRanked=edges,
                    fbid=ut['fbid'],
                    campaignId=self.campaign.pk,
                    contentId=self.content.pk,
                    numFace=self.num_face,
                    visit_id=notification_user.pk,
                    visit_type='targetshare.NotificationUser',
                    cache_match=self.cache,
                )[1].edges
            except IOError:
                logger.exception('Failed to filter {}'.format(ut['fbid']))
                self.failed_fbids.append(ut['fbid'])

            count += 1
            if count > 100:
                # Send 100 people to the csv and continue
                self._build_csv()

        self._build_csv()

    def _build_table(self, uuid, edges):
        ''' Method to build the HTML table that'll be included in the CSV
        that we send to clients. This table will later be embedded in an
        email that is sent to primaries, thus all the inline styles
        '''
        faces_path = reverse('faces-email', args=[uuid])
        if not self.url:
            faces_url = 'http://{}.{}{}'.format(
                self.client.subdomain,
                self.client.domain,
                faces_path,
            )
        else:
            faces_url = '{}?efuuid={}'.format(self.url, uuid)
        table_str = render_to_string('targetshare/faces_email_table.html', {
            'edges': edges,
            'faces_url': faces_url,
            'num_face': self.num_face
        })

        return table_str.encode('utf8', 'ignore')

    def _write_events(self, uuid, collection):
        notification_user = relational.NotificationUser.objects.get(uuid=uuid)
        events = []
        for edge in collection[:self.num_face]:
            events.append(
                relational.NotificationEvent(
                    notification_user_id=notification_user.pk,
                    campaign_id=self.campaign.pk,
                    client_content_id=self.content.pk,
                    friend_fbid=edge.secondary.id,
                    event_type='shown',
                )
            )

        for edge in collection[self.num_face:]:
            events.append(
                relational.NotificationEvent(
                    notification_user_id=notification_user.pk,
                    campaign_id=self.campaign.pk,
                    client_content_id=self.content.pk,
                    friend_fbid=edge.secondary.id,
                    event_type='generated',
                )
            )

        db.bulk_create.delay(events)

    def _build_csv(self):
        ''' Handles building out the CSV '''
        for uuid, collection in self.edge_collection.iteritems():
            primary = collection[0].primary
            row = [primary.id, primary.email]
            friend_list = []
            for edge in collection[:self.num_face]:
                friend_list.append(edge.secondary)

            fbids = [x.id for x in friend_list]

            row.append(fbids)
            row.append(lexical_list(
                [x.fname.encode('utf8', 'ignore') for x in friend_list[:3]])
            )
            row.append(self._build_table(uuid, collection[:self.num_face]))
            self._write_events(uuid, collection)
            self.csv_writer.writerow(row)

        self.file_handle.flush()
        self.edge_collection = {}
