import os
import csv
import logging
import hashlib
import multiprocessing
from tempfile import mkstemp
from decimal import Decimal
from optparse import make_option

from django.core.urlresolvers import reverse
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.db import connection, transaction
from django.utils import timezone

from targetshare.models import dynamo, relational
from targetshare.tasks import db, ranking
from targetshare.templatetags.string_format import lexical_list
from targetshare.integration.facebook.client import BadChunksError

logger = logging.getLogger(__name__)


def handle_star_threaded(args):
    # In python3.3 we get pool.starmap and this can die in a fire. Until then,
    # SIGH
    return handle_threaded(*args)


def handle_threaded(notification_id, campaign_id, content_id, mock, num_face,
               url, cache, offset, count):
    notification = relational.Notification.objects.get(pk=notification_id)
    campaign = relational.Campaign.objects.get(pk=campaign_id)
    content = relational.ClientContent.objects.get(pk=content_id)
    filename = build_csv(
        crawl_and_filter(
            campaign, content, notification, offset,
            count, num_face, cache, mock
        ),
        num_face, campaign, content, url=url
    )
    return filename


def build_csv(row_data, num_face, campaign, content, url=None):
    ''' Handles building out the CSV '''
    fd, filename = mkstemp()
    with open(filename, 'wb') as f:
        csv_writer = csv.writer(f)
        for uuid, collection in row_data:
            primary = collection[0].primary
            row = [primary.fbid, primary.email]

            friend_list = [edge.secondary for edge in collection[:num_face]]
            row.append([x.fbid for x in friend_list])
            row.append(lexical_list(
                [x.fname.encode('utf8', 'ignore') for x in friend_list[:3]])
            )

            row.append(build_table(
                uuid, collection[:num_face], num_face, url, campaign.client
            ))

            write_events(campaign, content, uuid, collection, num_face)
            csv_writer.writerow(row)

    os.close(fd)
    return filename


def build_table(uuid, edges, num_face, url=None, client=None):
    ''' Method to build the HTML table that'll be included in the CSV
    that we send to clients. This table will later be embedded in an
    email that is sent to primaries, thus all the inline styles
    '''
    faces_path = reverse('faces-email', args=[uuid])
    if not url:
        faces_url = 'http://{}.{}{}'.format(
            client.subdomain,
            client.domain,
            faces_path,
        )
    else:
        faces_url = '{}?efuuid={}'.format(url, uuid)
    table_str = render_to_string('targetshare/faces_email_table.html', {
        'edges': edges,
        'faces_url': faces_url,
        'num_face': num_face
    })

    return table_str.encode('utf8', 'ignore')


def crawl_and_filter(campaign, content, notification, offset,
                      end_count, num_face, cache=False, mock=False):
    ''' Grabs all of the tokens for a given UserClient, and throws them
    through the px4 crawl again
    '''
    logger.info(
        'Gathering list of users to crawl. Offset {}, end count {}'.format(
        offset, end_count
        )
    )
    failed_fbids = []
    client = campaign.client
    ucs = client.userclients.order_by('fbid')
    end_count = end_count or ucs.count()
    ucs = ucs[offset:end_count]
    user_fbids = [{
        'fbid': Decimal(x),
        'appid': client.fb_app_id,
    } for x in ucs.values_list('fbid', flat=True)]
    user_tokens = dynamo.Token.items.batch_get(keys=user_fbids)
    for count, ut in enumerate(user_tokens, 1):
        if timezone.now() >= ut.expires:
            logger.debug('FBID {} has expired token'.format(ut.fbid))
            continue

        logger.info('Crawling user {} of {}. FBID: {}'.format(
            count, end_count - offset, ut.fbid)
        )
        hash_str = hashlib.md5('{}{}{}{}'.format(
            ut['fbid'], campaign.pk,
            content.pk, notification.pk
        )).hexdigest()
        notification_user, created = relational.NotificationUser.objects.get_or_create(
            uuid=hash_str, fbid=ut['fbid'], notification=notification
        )
        try:
            edges = ranking.proximity_rank_four(
                mockMode=mock,
                fbid=ut['fbid'],
                token=ut
            )
        except (IOError, BadChunksError):
            logger.exception('Failed to crawl {}'.format(ut['fbid']))
            failed_fbids.append(ut['fbid'])
            continue

        try:
            edges = ranking.perform_filtering(
                edgesRanked=edges,
                fbid=ut['fbid'],
                campaignId=campaign.pk,
                contentId=content.pk,
                numFace=num_face,
                visit_id=notification_user.pk,
                visit_type='targetshare.NotificationUser',
                cache_match=cache,
            )[1].edges
            yield hash_str, edges
        except IOError:
            logger.exception('Failed to filter {}'.format(ut['fbid']))
            failed_fbids.append(ut['fbid'])
            continue
        except AttributeError:
            logger.exception('{} had too few friends'.format(ut['fbid']))
            failed_fbids.append(ut['fbid'])
            continue

    logger.info('Failed fbids: {}'.format(failed_fbids))


def write_events(campaign, content, uuid, collection, num_face):
    notification_user = relational.NotificationUser.objects.get(uuid=uuid)
    events = []
    for edge in collection[:num_face]:
        events.append(
            relational.NotificationEvent(
                notification_user_id=notification_user.pk,
                campaign_id=campaign.pk,
                client_content_id=content.pk,
                friend_fbid=edge.secondary.fbid,
                event_type='shown',
            )
        )

    for edge in collection[num_face:]:
        events.append(
            relational.NotificationEvent(
                notification_user_id=notification_user.pk,
                campaign_id=campaign.pk,
                client_content_id=content.pk,
                friend_fbid=edge.secondary.fbid,
                event_type='generated',
            )
        )

    db.bulk_create.delay(events)


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
        make_option(
            '-f', '--offset',
            help='Offset value of the Userclient table',
            dest='offset',
            default=0,
            type='int',
        ),
        make_option(
            '-p', '--people',
            help='Number of people to include',
            dest='count',
            type='int',
        ),
        make_option(
            '-w', '--workers',
            help='Number of threads to run [1]',
            dest='workers',
            type='int',
            default=1
        ),
    )

    def handle(self, campaign_id, content_id, mock, num_face,
               url, cache, offset, count, workers, **options):
        # DB objects
        campaign = relational.Campaign.objects.get(pk=campaign_id)
        content = relational.ClientContent.objects.get(pk=content_id)
        client = campaign.client

        notification = relational.Notification.objects.create(
            campaign=campaign,
            client_content=content
        )
        people_count = count if count else client.userclients.count()
        worker_slice = people_count / workers
        worker_args = []
        worker_offset = offset
        worker_end_count = offset + worker_slice
        # The threads freak out over the database connection, killing it
        # here causes each thread to end up with their own db connection.
        transaction.commit_unless_managed()
        connection.close()
        for x in xrange(1, (workers + 1)):
            if x == workers:
                worker_end_count = people_count
            worker_args.append(
                [
                    notification.pk, campaign.pk, content.pk,
                    mock, num_face, url, cache, worker_offset,
                    worker_end_count
                ]
            )
            worker_offset += worker_slice
            worker_end_count += worker_slice

        pool = multiprocessing.Pool(workers)
        filenames = pool.map(handle_star_threaded, worker_args)
        pool.terminate()
        self.stdout.write(
            'primary_fbid,email,friend_fbids,names,html_table\n')
        for fn in filenames:
            self.stdout.write(open(fn).read())
            os.remove(fn)
        logger.info('Completed faces email run')
