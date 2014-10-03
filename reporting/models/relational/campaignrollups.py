from django.db import models
from .metrics import Metrics


class Campaignrollups(Metrics):
    campaign_id = models.PositiveIntegerField()

    class Meta(object):
        app_label = 'reporting'
        db_table = 'campaignrollups'
