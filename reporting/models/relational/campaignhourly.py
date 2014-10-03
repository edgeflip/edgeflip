from django.db import models
from .metrics import Metrics


class Campaignhourly(Metrics):
    campaign_id = models.PositiveIntegerField()
    hour = models.DateTimeField()

    class Meta(object):
        app_label = 'reporting'
        db_table = 'campaignhourly'
