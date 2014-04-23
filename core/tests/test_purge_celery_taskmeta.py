from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command

from djcelery import models


class TestPurgeCeleryTaskMeta(TestCase):

    def setUp(self):
        super(TestPurgeCeleryTaskMeta, self).setUp()
        statuses = [
            'PENDING', 'STARTED', 'RETRY', 'FAILURE', 'SUCCESS'
        ]
        # Create old tasks
        for (count, status) in enumerate(statuses):
            models.TaskMeta.objects.create(
                status=status,
                hidden=False,
                task_id=count
            )

        # Avoiding the auto_now on date_done field
        models.TaskMeta.objects.update(
            date_done=timezone.now() - timedelta(days=5)
        )

    def test_purge_clears_completed_tasks(self):
        ''' Purges SUCCESS/FAILURE jobs, leaves the rest available '''
        self.assertEqual(models.TaskMeta.objects.count(), 5)
        call_command('purge_celery_taskmeta')
        self.assertEqual(models.TaskMeta.objects.count(), 3)
        self.assertFalse(
            models.TaskMeta.objects.filter(
                status__in=['FAILURE', 'SUCCESS']).exists(),
        )

    def test_purge_only_clears_expired_objects(self):
        ''' Asserts that newer objects above the expired threshold will
        survive. `date_done` on TaskMeta is an auto_now DateTimeField, so our
        new object will have timezone.now() as its timestamp
        '''
        tm = models.TaskMeta.objects.create(
            status='SUCCESS', task_id=123, hidden=False)
        self.assertEqual(models.TaskMeta.objects.count(), 6)
        call_command('purge_celery_taskmeta')
        self.assertEqual(models.TaskMeta.objects.count(), 4)
        self.assertTrue(
            models.TaskMeta.objects.filter(
                status__in=['FAILURE', 'SUCCESS']).exists(),
        )
        self.assertTrue(
            models.TaskMeta.objects.filter(pk=tm.pk).exists()
        )
