import csv
import logging
import time
from decimal import Decimal
from optparse import make_option
from datetime import datetime

import celery

from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from targetshare.models import dynamo, relational
from targetshare.tasks import ranking

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
            '-c', '--civis-threshold',
            help='Threshold of missing friends in civis cache [5]',
            dest='civis_count',
            default=5,
            type='int',
        ),
        make_option(
            '-b', '--bucket',
            help='S3 Bucket to check for cache [civis_cache]',
            dest='bucket',
            default='civis_cache'
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

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError(
                'Command expects 2 args, 1 campaign ID and 1 content ID. '
                '%s args provided: %s' % (
                    len(args),
                    ' '.join(str(x) for x in args)
                )
            )

        # DB objects
        self.campaign = relational.Campaign.objects.get(pk=args[0])
        self.content = relational.ClientContent.objects.get(pk=args[1])
        self.client = self.campaign.client
        self.visit = relational.Visit.objects.create(
            session_id='%s-%s-%s' % (
                datetime.now().strftime('%m-%d-%y_%H:%M:%S'),
                args[0],
                args[1]
            ),
            app_id=self.client.fb_app_id,
            ip='127.0.0.1',
            fbid=None,
            source='faces_email',
        )

        # Settings
        self.mock = options['mock']
        self.civis_count = options['civis_count']
        self.num_face = options['num_face']
        self.filename = options.get('output') or 'faces_email_%s.csv' % datetime.now().strftime('%m-%d-%y_%H:%M:%S')
        self.task_list = []
        self.edge_collection = []

        # Process information
        self._crawl_and_filter()
        self._crawl_status_handler()
        self._build_csv()

    def _crawl_and_filter(self):
        logger.info('Gathering list of users to crawl')
        user_fbids = [{
            'fbid': Decimal(x),
            'appid': self.client.fb_app_id,
        } for x in self.client.userclients.values_list('fbid', flat=True)]
        user_tokens = dynamo.Token.items.batch_get(keys=user_fbids)
        for ut in user_tokens:
            self.task_list.append(
                ranking.proximity_rank_three(
                    mock_mode=self.mock,
                    fbid=ut['fbid'],
                    token=ut,
                    visit_id=self.visit.pk,
                    campaignId=self.campaign.pk,
                    contentId=self.content.pk,
                    numFace=self.num_face,
                    faces_email=True
                )
            )
        logger.info('Crawling %s users', str(len(self.task_list)))

    def _crawl_status_handler(self):
        error_count = 0
        conn = connections.all()[0]
        while self.task_list:
            logger.info('Checking status of %s tasks', str(len(self.task_list)))
            for task_id in self.task_list:
                conn.commit_unless_managed()
                task = celery.current_app.AsyncResult(task_id)
                if task.ready():
                    if task.successful():
                        self.edge_collection.append(task.result[1].edges) # Filtered friends
                    else:
                        error_count += 1
                        logger.error('Task Failed: %s' % task.traceback)
                    self.task_list.remove(task)
                    logger.info('Finished task')
                time.sleep(1)
        logger.info(
            'Completed crawling users with %s failed tasks',
            str(error_count)
        )

    def _build_csv(self):
        with open(self.filename, 'wb') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([
                'primary_fbid', 'email', 'friend_fbids'
            ])
            for collection in self.edge_collection:
                primary = collection[0].primary
                row = [primary.id, primary.email]
                friend_list = []
                for edge in collection[:self.num_face]:
                    friend_list.append(edge.secondary.id)

                row.append(friend_list)
                csv_writer.writerow(row)
