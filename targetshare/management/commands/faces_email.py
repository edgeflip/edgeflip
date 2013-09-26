import json
import logging
import time
from decimal import Decimal
from optparse import make_option

import boto

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from targetshare.models import dynamo, relational
from targetshare.tasks import ranking
from targetshare import utils

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = '<client_id> <filter_id>'
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
        )
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

        # Client Setup
        self.client = relational.Client.objects.get(pk=args[0])
        self.filter_obj = relational.Filter.objects.get(pk=args[1])
        self.mock = options['mock']
        self.civis_count = options['civis_count']
        self.task_list = []
        self.edge_collection = []

        # S3 Setup
        self.s3_conn = boto.connect_s3()
        self.bucket = self.s3_conn.get_bucket(options['bucket'])

        # Process information
        self._crawl_and_filter()
        self._crawl_status_handler()
        self.edge_collection = self._filter_edges()
        import ipdb; ipdb.set_trace() ### XXX BREAKPOINT
        print 'wut'

    def _crawl_and_filter(self):
        logger.info('Gathering list of users to crawl')
        user_fbids = [{
            'fbid': Decimal(x),
            'appid': self.client.fb_app_id,
        } for x in self.client.userclients.values_list('fbid', flat=True)]
        user_tokens = dynamo.Token.items.batch_get(keys=user_fbids)
        for ut in user_tokens:
            # Does it make sense to throw these things on the celery queue?
            # Also note, that checking the status of tasks wasn't successful
            # for me in testing from a command line script.
            self.task_list.append(
                ranking.px3_crawl.delay(
                    self.mock,
                    ut['fbid'],
                    ut
                )
            )
        logger.info('Crawling %s users', str(len(self.task_list)))

    def _crawl_status_handler(self):
        error_count = 0
        conn = connections.all()[0]
        while self.task_list:
            logger.info('Checking status of %s tasks', str(len(self.task_list)))
            for task in self.task_list:
                conn.commit_unless_managed()
                if task.ready():
                    if task.successful():
                        self.edge_collection.append(task.result)
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

    def _filter_edges(self):
        logger.info('Starting filtering process')
        filtered_edge_collection = []
        if not self.filter_obj.filterfeatures.exists():
            return self.edge_collection

        for ff in self.filter_obj.filterfeatures.all():
            for edges in self.edge_collection:
                if ff.feature in settings.CIVIS_FILTERS:
                    self._civis_match_filter(edges, ff)
                else:
                    edges = [
                        x for x in edges if ff.filter._standard_filter(
                            x.secondary, ff.feature, ff.operator, ff.value
                        )
                    ]

                filtered_edge_collection.append(edges)

        return filtered_edge_collection
        logger.info('Filtering process completed')

    def _civis_match_filter(self, edges, feature):
        missing_count = 0
        valid_edges = []
        for edge in edges:
            user = edge.secondary
            key = self.bucket.get_key(user.id)
            if not key:
                missing_count += 1
                if missing_count >= self.civis_count:
                    break
                continue

            result = json.loads(key.get_contents_as_string())
            scores_dict = result.get('results', {}).get('scores')
            score = scores_dict.get(feature.feature) or {}
            if score and float(score.get(feature.operator, 0)) >= float(feature.value):
                valid_edges.append(edge)

        if missing_count >= self.civis_count:
            edges = utils.civis_filter(
                edges, feature.feature, feature.operator, feature.value
            )

        return edges
