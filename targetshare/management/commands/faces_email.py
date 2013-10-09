import csv
import logging
import time
import hashlib
from decimal import Decimal
from optparse import make_option
from datetime import datetime

import celery

from django.db import transaction
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
    )

    def handle(self, campaign_id, content_id, mock, num_face, output, **options):
        # DB objects
        self.campaign = relational.Campaign.objects.get(pk=campaign_id)
        self.content = relational.ClientContent.objects.get(pk=content_id)
        self.client = self.campaign.client

        # Settings
        self.mock = mock
        self.num_face = num_face
        self.filename = output if output else 'faces_email_%s.csv' % datetime.now().strftime('%m-%d-%y_%H:%M:%S')
        self.task_list = {}
        self.edge_collection = {}
        self.notification = relational.Notification.objects.create(
            campaign=self.campaign,
            client_content=self.content
        )

        # Process information
        self._crawl_and_filter()
        self._crawl_status_handler()
        self._build_csv()

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
        for ut in user_tokens:
            hash_str = hashlib.md5('{}{}{}{}'.format(
                ut['fbid'], self.campaign.pk,
                self.content.pk, self.notification.pk
            )).hexdigest()
            notification_user, created = relational.NotificationUser.objects.get_or_create(
                uuid=hash_str, fbid=ut['fbid'], notification=self.notification
            )
            self.task_list[notification_user.uuid] = ranking.proximity_rank_three(
                mock_mode=self.mock,
                fbid=ut['fbid'],
                token=ut,
                visit_id=notification_user.pk,
                campaignId=self.campaign.pk,
                contentId=self.content.pk,
                numFace=self.num_face,
                visit_type='targetshare.NotificationUser',
                s3_match=True
            )
        logger.info('Crawling %s users', str(len(self.task_list)))

    def _crawl_status_handler(self):
        ''' Simple method for watching the tasks we're waiting on to complete.
        Just iterates over the list of tasks and reports their status
        '''
        error_count = 0
        while self.task_list:
            logger.info('Checking status of %s tasks', str(len(self.task_list)))
            for uuid, task in self.task_list.items():
                transaction.commit_unless_managed()
                if task.ready():
                    if task.successful():
                        self.edge_collection[uuid] = task.result[1].edges
                    else:
                        error_count += 1
                        logger.error('Task %s Failed: %s',
                            task.id, task.traceback)
                    del self.task_list[uuid]
                    logger.debug('Finished task: %s' % task.id)
                else:
                    if task.parent and task.parent.ready() and not task.parent.successful():
                        # Tripped an error somewhere in the chain
                        # but the chain task has no idea
                        # See: https://github.com/celery/celery/issues/1014
                        error_count += 1
                        logger.error('Task %s Failed: %s',
                            task.parent.id, task.parent.traceback)
                        del self.task_list[uuid]
            time.sleep(1)
        logger.info(
            'Completed crawling users with %s failed tasks',
            str(error_count)
        )

    def _build_table(self, uuid, edges):
        ''' Method to build the HTML table that'll be included in the CSV
        that we send to clients. This table will later be embedded in an
        email that is sent to primaries, thus all the inline styles
        '''
        faces_base_url = reverse('faces-email', args=[uuid])
        faces_url = 'http://{}.{}{}'.format(
            self.client.subdomain,
            self.client.domain,
            faces_base_url,
        )
        table_str = render_to_string('targetshare/faces_email_table.html', {
            'edges': edges,
            'faces_url': faces_url,
            'num_face': self.num_face
        })

        return table_str

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
        with open(self.filename, 'wb') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([
                'primary_fbid', 'email', 'friend_fbids', 'names', 'html_table'
            ])
            for uuid, collection in self.edge_collection.iteritems():
                primary = collection[0].primary
                row = [primary.id, primary.email]
                friend_list = []
                for edge in collection[:self.num_face]:
                    friend_list.append(edge.secondary)

                fbids = [x.id for x in friend_list]

                row.append(fbids)
                row.append(lexical_list([x.fname for x in friend_list[:3]]))
                row.append(self._build_table(uuid, collection[:self.num_face]))
                self._write_events(uuid, collection)
                csv_writer.writerow(row)
