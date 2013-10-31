import logging
from decimal import Decimal
from optparse import make_option

import us
import requests

from django.core.management.base import BaseCommand

from civis_matcher import matcher

from targetshare.integration.facebook import client as facebook
from targetshare.models import dynamo, relational

logger = logging.getLogger(__name__)
TIME_FORMAT = '%m-%d-%y_%H:%M:%S'


class Command(BaseCommand):
    args = '<client_id>'
    help = 'Command for seeding cache for Faces email'
    option_list = BaseCommand.option_list + (
        make_option(
            '-d', '--days',
            dest='days',
            help='Number of days old a cache object is allowed to be, default 30',
            default=30,
            type='int',
        ),
    )

    def handle(self, client_id, days, **options):
        # At some point we may wish to add a filtering element to this, which
        # could take some load off of Civis servers. For the time being,
        # we're holding off.
        self.client = relational.Client.objects.get(pk=client_id)
        self.days = days
        logger.info('Performing matches')
        self._perform_matching(self._retrieve_users())
        logger.info('Cache successfully seeded')

    def _retrieve_users(self):
        ''' Retrieve all of the users that we need to crawl and cache '''
        user_fbids = [{
            'fbid': Decimal(x),
            'appid': self.client.fb_app_id,
        } for x in self.client.userclients.values_list('fbid', flat=True)]
        user_tokens = dynamo.Token.items.batch_get(keys=user_fbids)
        logger.info('Retrieving edges for %s users', len(user_fbids))
        for ut in user_tokens:
            try:
                user = facebook.get_user(ut['fbid'], ut['token'])
                yield facebook.get_friend_edges(
                    user,
                    ut['token'],
                    require_incoming=False,
                    require_outgoing=False,
                )
            except IOError:
                continue

    def _perform_matching(self, edge_collection):
        for primary in edge_collection:
            people_dict = {'people': {}}
            prim_user = primary[0].primary
            prim_state = us.states.lookup(prim_user.state) if prim_user.state else ''
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
            people_dict['people'][str(prim_user.fbid)] = prim_dict
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
                if state:
                    user_dict['state'] = state.abbr
                user_dict['city'] = user.city
                user_dict['first_name'] = user.fname
                user_dict['last_name'] = user.lname
                people_dict['people'][str(user.fbid)] = user_dict

            try:
                cm = matcher.CivisMatcher()
                results = cm.bulk_match(people_dict, raw=True)
            except requests.RequestException:
                logger.exception('Failed to contact Civis (%s)', prim_user.fbid)
            except matcher.MatchException:
                logger.exception('Matcher Error! (%s)', prim_user.fbid)
            except Exception:
                logger.exception('Unknown error (%s)', prim_user.fbid)
            else:
                with dynamo.CivisResult.items.batch_write() as batch:
                    for fbid, result in results.iteritems():
                        batch.put_item(fbid=fbid, result=result)
