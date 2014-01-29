from __future__ import absolute_import

import os

from celery import Celery

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
    print('Request: {0!r}'.format(self.request))
