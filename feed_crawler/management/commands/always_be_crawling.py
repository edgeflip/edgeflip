import logging
from datetime import datetime

from django.core.management.base import NoArgsCommand

from targetshare.models import dynamo
from feed_crawler import tasks


logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = "Starts the crawler service"

    def handle_noargs(self, *args, **options):
        logger.info('Starting up...')
        self.crawl()

    def crawl(self):
        logger.info('Starting crawl of all tokens')
        count = 0
        for token in dynamo.Token.items.scan(expires__gt=datetime.now()):
            logger.info('Crawling token for {}'.format(token.fbid))
            tasks.crawl_user(token)
            count += 1
        logger.info('Placed {} tokens on the queue'.format(count + 1))
