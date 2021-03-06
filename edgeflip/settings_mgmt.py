"""Settings particularly suited to running management commands.

Enable these with the "settings" option:

 python manage.py mycommand --settings=edgeflip.settings_mgmt

"""
from edgeflip.settings import *


CELERY_MAX_CACHED_RESULTS = 1
