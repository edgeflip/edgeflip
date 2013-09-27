import logging
from decimal import Decimal
from optparse import make_option
from datetime import datetime, timedelta

import us
import requests

import boto
from boto.exception import S3ResponseError

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from civis_matcher import matcher

from targetshare import facebook
from targetshare.models import dynamo, relational

logger = logging.getLogger(__name__)
TIME_FORMAT = '%m-%d-%y_%H:%M:%S'


class Command(BaseCommand):
    args = '<client_id> <filter_id>'
    help = 'Command for seeding cache for Faces email'
    option_list = BaseCommand.option_list + (
        make_option(
            '-b', '--bucket',
            dest='bucket',
            help='Name of S3 bucket to use. Default "civis_cache"',
            default='civis_cache'
        ),
        make_option(
            '-d', '--days',
            dest='days',
            help='Number of days old a cache object is allowed to be, default 30',
            default=30,
            type='int',
        ),
    )

    def handle(self, *args, **options):
        # TODO: Verify if the Filter ID plays any role at all. Hard to see
        # how it would. Why filter people out? Just match and cache it all.
        if len(args) != 2:
            raise CommandError(
                'Command expects 2 args, 1 client ID and 1 filter ID. '
                '%d args provided: %s' % (
                    len(args),
                    ' '.join(str(x) for x in args)
                )
            )
        self.client = relational.Client.objects.get(pk=args[0])
        self.filter_obj = relational.Filter.objects.get(pk=args[1])
        self.cache_age = datetime.now() - timedelta(days=options['days'])
        self.s3_conn = boto.connect_s3(
            settings.AWS.AWS_ACCESS_KEY_ID,
            settings.AWS.AWS_SECRET_ACCESS_KEY
        )
        logger.info(
            'Start cache seed with bucket %s, client %s, filter %s.',
            options['bucket'], self.client.name, self.filter_obj.name
        )
        self.bucket = self._get_bucket(options['bucket'])
        self.edges = self._retrieve_users()
        logger.info('Performing matches')
        self._perform_matching(self.edges)
        logger.info('Cache successfully seeded')

    def _retrieve_users(self):
        ''' Retrieve all of the users that we need to crawl and cache '''
        user_fbids = [{
            'fbid': Decimal(x),
            'appid': self.client.fb_app_id,
        } for x in self.client.userclients.values_list('fbid', flat=True)]
        user_tokens = dynamo.Token.items.batch_get(keys=user_fbids)
        edge_collection = []
        logger.info('Retrieving edges for %s users', len(user_fbids))
        for ut in user_tokens:
            edge_collection.append(
                facebook.getFriendEdgesFb(
                    ut['fbid'],
                    ut['token'],
                    requireIncoming=False,
                    requireOutgoing=False
                )
            )
        return edge_collection

    def _get_bucket(self, bucket_name):
        ''' Retrieves bucket if it exists, otherwise creates it '''
        try:
            bucket = self.s3_conn.get_bucket(bucket_name)
        except S3ResponseError:
            try:
                bucket = self.s3_conn.create_bucket(bucket_name)
            except S3ResponseError:
                self.stderr.write(
                    'Failed to obtain connection to bucket: %s' % bucket_name
                )
                raise

        return bucket

    def _perform_matching(self, edge_collection):
        for primary in edge_collection:
            people_dict = {'people': {}}
            prim_user = primary[0].primary
            prim_state = us.states.lookup(prim_user.state)
            prim_dict = {
                'state': prim_state.abbr if prim_state else None,
                'city': prim_user.city,
                'first_name': prim_user.fname,
                'last_name': prim_user.lname
            }
            if prim_user.birthday:
                prim_dict.update({
                    'birth_month': '%02d' % prim_user.birthday.month,
                    'birth_year': str(prim_user.birthday.year),
                    'birth_day': '%02d' % prim_user.birthday.day,
                })
            people_dict[str(prim_user.id)] = prim_dict
            for edge in primary:
                user = edge.secondary
                user_dict = {}
                if user.birthday:
                    user_dict['birth_month'] = '%02d' % user.birthday.month
                    user_dict['birth_year'] = str(user.birthday.year)
                    user_dict['birth_day'] = '%02d' % user.birthday.day

                if not user.state or not user.city:
                    continue

                state = us.states.lookup(user.state)
                user_dict['state'] = state.abbr if state else None
                user_dict['city'] = user.city
                user_dict['first_name'] = user.fname
                user_dict['last_name'] = user.lname
                people_dict['people'][str(user.id)] = user_dict

            try:
                cm = matcher.S3CivisMatcher(
                    settings.AWS.AWS_ACCESS_KEY_ID,
                    settings.AWS.AWS_SECRET_ACCESS_KEY
                )
                results = cm.bulk_match(people_dict, raw=True)
            except requests.RequestException:
                logger.exception('Failed to contact Civis')
                return []
            except matcher.MatchException:
                logger.exception('Matcher Error!')
                return []

            return results
