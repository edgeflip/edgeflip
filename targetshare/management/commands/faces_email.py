import os
import csv
import logging
import hashlib
import multiprocessing
from tempfile import mkstemp
from decimal import Decimal
from optparse import make_option
from collections import defaultdict

from django.core.urlresolvers import reverse
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.db import connection
from django.utils import timezone

from targetshare.models import dynamo, relational
from targetshare.tasks import db, targeting
from targetshare.templatetags.string_format import lexical_list


LOG = logging.getLogger(__name__)


def handle_star_threaded(args):
    # In python3.3 we get pool.starmap and this can die in a fire. Until then,
    # SIGH
    return handle_threaded(*args)


def handle_threaded(notification_id, campaign_id, content_id, mock, num_face,
               url, cache, offset, count):
    notification = relational.Notification.objects.get(pk=notification_id)
    campaign = relational.Campaign.objects.get(pk=campaign_id)
    content = relational.ClientContent.objects.get(pk=content_id)
    error_dict = defaultdict(int)
    filename = build_csv(
        crawl_and_filter(
            campaign, content, notification, offset,
            count, num_face, error_dict, cache, mock
        ),
        num_face, campaign, content, url=url
    )
    return filename, error_dict


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
    faces_path = reverse('targetshare:faces-email', args=[uuid])
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
                      end_count, num_face, error_dict, cache=False, mock=False):
    ''' Grabs all of the tokens for a given UserClient, and throws them
    through the px4 crawl again
    '''
    LOG.info('Gathering list of users to crawl: offset %s, end count %s', offset, end_count)
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
    for (count, ut) in enumerate(user_tokens, 1):
        if timezone.now() >= ut.expires:
            LOG.debug('FBID %s has expired token', ut.fbid)
            continue

        LOG.info('Crawling user %s of %s; FBID: %s',
                 count, end_count - offset, ut.fbid)
        seed = ''.join(str(part) for part in (
            ut.fbid, campaign.pk, content.pk, notification.pk,
        ))
        hash_ = hashlib.md5(seed).hexdigest()
        (notification_user, _created) = notification.notificationusers.get_or_create(
            uuid=hash_, fbid=ut.fbid)

        try:
            (stream, edges) = targeting.px4_crawl(ut)
        except Exception as exc:
            LOG.exception('Failed to crawl %s', ut.fbid)
            failed_fbids.append(ut.fbid)
            error_dict[exc.__class__.__name__] += 1
            continue

        filtered_result = targeting.px4_filter(
            stream,
            edges,
            campaign.pk,
            content.pk,
            ut.fbid,
            notification_user.pk,
            num_face,
            visit_type='targetshare.NotificationUser',
            cache_match=cache,
            force=True,
        )
        reranked_result = targeting.px4_rank(filtered_result)
        targeted_edges = reranked_result.filtered and reranked_result.filtered.edges

        if targeted_edges:
            yield (hash_, targeted_edges)
        else:
            LOG.warning('User %s had too few friends', ut.fbid)
            failed_fbids.append(ut.fbid)

    if failed_fbids:
        LOG.info('Failed users: %r', failed_fbids)


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
            help='Number of workers to run [1]',
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
        people_count = count or client.userclients.count()
        worker_slice = people_count / workers
        worker_args = []
        # The workers freak out over the database connection, killing it
        # here causes each workers to end up with their own db connection.
        connection.close()
        for x in xrange(workers):
            worker_offset = offset + x * worker_slice
            worker_end_count = people_count if x == workers - 1 else worker_offset + worker_slice
            worker_args.append(
                [
                    notification.pk, campaign.pk, content.pk,
                    mock, num_face, url, cache, worker_offset,
                    worker_end_count
                ]
            )

        pool = multiprocessing.Pool(workers)
        results = pool.map(handle_star_threaded, worker_args)
        pool.terminate()
        self.stdout.write(
            'primary_fbid,email,friend_fbids,names,html_table\n')
        total_errors = defaultdict(int)
        for (filename, errors) in results:
            self.stdout.write(open(filename).read())
            os.remove(filename)
            for key in errors.keys():
                total_errors[key] += errors[key]

        for key, value in total_errors.iteritems():
            LOG.info('{} total {} errors'.format(value, key))
        LOG.info('Completed faces email run')
