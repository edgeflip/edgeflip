import itertools
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

        tokens = dynamo.Token.items.scan(expires__gt=timezone.now())
        # Tokens should already be sorted by fbid (hash); group-by:
        users_tokens = itertools.groupby(tokens, lambda token: token.fbid)

        count = 0
        for (count, (fbid, user_tokens)) in enumerate(users_tokens, 1):
            # Of all apps' tokens for user, use freshest:
            token = sorted(user_tokens, key=lambda token: token.expires)[-1]
            logger.debug('Crawling token %s', token)
            tasks.crawl_user.delay(fbid, token.appid)

        logger.info('Placed %s tokens on the queue', count)
