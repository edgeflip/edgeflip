from django.db import models
from .metrics import Metrics

class Campaignstats(Metrics):
    campaign_id = models.PositiveIntegerField()

    class Meta(object):
        app_label = 'reporting'
        db_table = 'campaignstats'
