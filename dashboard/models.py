from django.db import models

class CampaignSum(models.Model):
    """ all of the data for a particular campaign in daily increments """

    # ForeignKey to proper campaigns in the near future
    campaign = models.CharField(max_length=256, blank=True)


    data = models.TextField(max_length=500)  # and we jam our data in here as json


    class Meta(object):
        db_table = 'sum_campaign'


class DaySum(models.Model):
    """ A day's worth of data in hourly increments """

    # ForeignKey to proper campaigns in the near future
    campaign = models.CharField(max_length=256, blank=True)

    day = models.DateField()
    data = models.TextField(max_length=500)  # ghetto json field .. fixed size, we could CharField here


    class Meta(object):
        db_table = 'sum_day'
