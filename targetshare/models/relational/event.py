from django.db import models


class Event(models.Model):

    event_id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=128)
    campaign = models.ForeignKey('Campaign', null=True)
    client_content = models.ForeignKey(
        'ClientContent',
        db_column='content_id',
        null=True
    )
    ip = models.CharField(max_length=32)
    fbid = models.BigIntegerField(null=True)
    friend_fbid = models.BigIntegerField(null=True)
    event_type = models.CharField(max_length=64, db_column='type')
    app_id = models.BigIntegerField(db_column='appid')
    content = models.CharField(max_length=128)
    activity_id = models.BigIntegerField(null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            'session_id', 'campaign', 'content',
            'fbid', 'friend_fbid', 'activity_id'
        )
        db_table = 'events'
