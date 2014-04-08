import logging

from django.core.management.base import NoArgsCommand
from django.utils import timezone

from targetshare.models import dynamo
from feed_crawler import tasks


logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = "Starts the crawler service"

    def handle_noargs(self, **options):
        logger.info('Starting crawl of all tokens')
        count = 0
        tokens = dynamo.Token.items.scan(expires__gt=timezone.now())
        for (count, token) in enumerate(tokens, 1):
            logger.info('Crawling token %s', token)
            tasks.crawl_user.delay(token.fbid, token.appid)
        logger.info('Placed %s tokens on the queue', count)
