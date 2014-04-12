import itertools
import logging
import operator

from django.core.management.base import NoArgsCommand
from django.utils import timezone

from targetshare.models import dynamo
from feed_crawler import tasks


logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = "Starts the crawler service"

    def handle_noargs(self, **options):
        logger.info('Enqueuing crawl tasks for all users with active tokens')

        tokens = dynamo.Token.items.scan(expires__gt=timezone.now())
        # Tokens should already be grouped by hash (fbid); group-by:
        fbid_tokens = itertools.groupby(tokens, operator.attrgetter('fbid'))

        count = 0
        for (count, (fbid, _tokens)) in enumerate(fbid_tokens, 1):
            logger.debug('Crawling user %s', fbid)
            tasks.crawl_user.delay(fbid)

        logger.info('Enqueued %s tasks', count)
