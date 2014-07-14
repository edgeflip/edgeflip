from django.db import models
from .metrics import Metrics

class Clientrollups(Metrics):
    client_id = models.PositiveIntegerField()

    class Meta(object):
        app_label = 'reporting'
        db_table = 'clientrollups'
