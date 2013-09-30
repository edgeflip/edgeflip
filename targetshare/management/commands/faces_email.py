import csv
import logging
import time
from decimal import Decimal
from optparse import make_option
from datetime import datetime

import celery

from django.db import connections
from django.core.urlresolvers import reverse
from django.core.management.base import BaseCommand, CommandError

from targetshare import utils
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
        self.num_face = options['num_face']
        self.filename = options.get('output') or 'faces_email_%s.csv' % datetime.now().strftime('%m-%d-%y_%H:%M:%S')
        self.task_list = []
        self.edge_collection = []

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
        ''' Simple method for watching the tasks we're waiting on to complete.
        Just iterates over the list of tasks and reports their status
        '''
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
                    self.task_list.remove(task_id)
                    logger.info('Finished task')
                time.sleep(1)
        logger.info(
            'Completed crawling users with %s failed tasks',
            str(error_count)
        )

    def _build_table(self, edges):
        ''' Method to build the HTML table that'll be included in the CSV
        that we send to clients. This table will later be embedded in an
        email that is sent to primaries, thus all the inline styles
        '''
        faces_base_url = reverse('faces-email-encoded', args=[
            utils.encodeDES('{}/{}'.format(self.campaign.pk, self.content.pk))
        ])
        query_string = ''.join(
            ['friend_fbid={}&'.format(x.secondary.id) for x in edges]
        ).rstrip('&')
        query_string = '{}&fbid={}'.format(
            query_string, edges[0].primary.id
        )
        faces_url = 'http://{}.{}{}?{}'.format(
            self.client.subdomain,
            self.client.domain,
            faces_base_url,
            query_string
        )
        table_str = """
            <table align='center' border='0' cellpadding='0' style='border:5px solid #e4e6e0;background-color:#e4e6e0'
                <tbody>
        """
        user_cell = """
            <td style='border:6px solid #e4e6e0;background-color:#07304e'>
                <table border='0'>
                    <tbody>
                        <tr>
                            <td style='padding:6px;vertical-align:middle'>
                                <a href='{}' style='color:white;text-decoration:none' target='_blank'><img src='http://graph.facebook.com/{}/picture' border='0/'></a>
                            </td>
                            <td style='padding:6px'>
                                <a href='{}' style='text-decoration:none' target='_blank'><font color='white'>{} {}</font></a>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </td>
        """
        count = 0
        table_str = "{}<tr>".format(table_str)
        for edge in edges:
            if count == 3:
                # end the row and start a new one
                table_str = "{}</tr><tr>".format(table_str)
                count = 0

            user_str = user_cell.format(
                faces_url, edge.secondary.id, faces_url,
                edge.secondary.fname, edge.secondary.lname
            )
            table_str = "{}{}".format(table_str, user_str)
            count += 1

        table_str = "{}</tr></tbody></table>".format(table_str)

        return table_str

    def _build_csv(self):
        ''' Handles building out the CSV '''
        with open(self.filename, 'wb') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([
                'primary_fbid', 'email', 'friend_fbids', 'names', 'html_table'
            ])
            for collection in self.edge_collection:
                primary = collection[0].primary
                row = [primary.id, primary.email]
                friend_list = []
                for edge in collection[:self.num_face]:
                    friend_list.append(edge.secondary)

                fbids = [x.id for x in friend_list]
                names = [x.fname for x in friend_list]

                row.append(fbids)
                name_str = ''
                if len(names) == 1:
                    name_str = names[0]
                elif len(names) == 2:
                    name_str = ' and '.join(names)
                else:
                    name_str = '%s, %s, and %s' % (names[0], names[1], names[2])
                row.append(name_str)
                row.append(self._build_table(collection[:self.num_face]))
                csv_writer.writerow(row)
