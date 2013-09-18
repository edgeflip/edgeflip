from django.db import models


class Event(models.Model):

    event_id = models.AutoField(primary_key=True)
    visit = models.ForeignKey('Visit', related_name='events')
    event_type = models.CharField(max_length=64, db_column='type', null=True, blank=True)
    campaign = models.ForeignKey('Campaign', null=True)
    client_content = models.ForeignKey('ClientContent', db_column='content_id', null=True)
    content = models.CharField(max_length=128, blank=True)
    friend_fbid = models.BigIntegerField(null=True, blank=True)
    activity_id = models.BigIntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'events'
