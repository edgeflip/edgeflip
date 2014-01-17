from __future__ import absolute_import

import os

from celery import Celery
from celery.exceptions import MaxRetriesExceededError

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edgeflip.settings')

# Dropped below environ.setdefault to ensure the settings module is
# properly specified before importing
from django.conf import settings

app = Celery('edgeflip')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True, default_retry_delay=5, max_retries=2)
def debug_task(self):
    try:
        1/0
    except Exception as exc:
        print vars(self)
        try:
            self.retry()
        except MaxRetriesExceededError:
            print 'wut wut'
    #print('Request: {0!r}'.format(self.request))
