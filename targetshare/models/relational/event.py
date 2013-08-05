from django.db import models


class Event(models.Model):

    event_id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=128, blank=True)
    campaign = models.ForeignKey('Campaign', null=True)
    client_content = models.ForeignKey(
        'ClientContent',
        db_column='content_id',
        null=True
    )
    ip = models.CharField(max_length=32, blank=True)
    fbid = models.BigIntegerField(null=True, blank=True)
    friend_fbid = models.BigIntegerField(null=True, blank=True)
    event_type = models.CharField(max_length=64, db_column='type',
                                  null=True, blank=True)
    app_id = models.BigIntegerField(db_column='appid', null=True, blank=True)
    content = models.CharField(max_length=128, blank=True)
    activity_id = models.BigIntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        app_label = 'targetshare'
        unique_together = (
            'session_id', 'campaign', 'content',
            'fbid', 'friend_fbid', 'activity_id'
        )
        db_table = 'events'
