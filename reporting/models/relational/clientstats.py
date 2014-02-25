from django.db import models

class Clientstats(models.Model):
    
    campaign_id = models.PositiveIntegerField()
    hour = models.DateTimeField()
    visits = models.PositiveIntegerField()
    clicks = models.PositiveIntegerField()
    auths = models.PositiveIntegerField()
    uniq_auths = models.PositiveIntegerField()
    shown = models.PositiveIntegerField()
    shares = models.PositiveIntegerField()
    audience = models.PositiveIntegerField()
    clickbacks = models.PositiveIntegerField()

    class Meta(object):
        app_label = 'reporting'
        db_table = 'clientstats'
