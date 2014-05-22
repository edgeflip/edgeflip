import logging
from datetime import timedelta

from djcelery.models import TaskMeta

from django.conf import settings
from django.utils import timezone
from django.core.management.base import NoArgsCommand


logger = logging.getLogger(__name__)


class Command(NoArgsCommand):
    help = "Purges completed/failed tasks from the celery result tables"

    def handle_noargs(self, **options):
        delta = timedelta(seconds=settings.CELERY_TASK_RESULT_EXPIRES)
        logger.info(
            'Purging all celery tasks that have failed/succeeded '
            'and are over %s old', delta
        )
        TaskMeta.objects.filter(
            status__in=['SUCCESS', 'FAILURE'],
            date_done__lte=timezone.now() - delta
        ).delete()
        logger.info('Purge complete')
