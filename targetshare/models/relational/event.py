from django.db import models
from django.utils import timezone

from . import manager


class EventModel(models.Model):

    event_type = models.CharField(max_length=64, db_column='type')
    campaign = models.ForeignKey('Campaign', null=True)
    client_content = models.ForeignKey('ClientContent', db_column='content_id', null=True)
    content = models.CharField(max_length=1028, blank=True)
    friend_fbid = models.BigIntegerField(null=True, blank=True)
    activity_id = models.BigIntegerField(null=True, blank=True)
    event_datetime = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = manager.Manager()

    class Meta(object):
        abstract = True


class Event(EventModel):

    event_id = models.AutoField(primary_key=True)
    visit = models.ForeignKey('Visit', related_name='events')

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'events'

    def __unicode__(self):
        return u"{} [{}]".format(self.event_type, self.visit_id)


class NotificationEvent(EventModel):

    notification_event_id = models.AutoField(primary_key=True)
    notification_user = models.ForeignKey(
        'NotificationUser', related_name='events')

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'notification_events'

    def __unicode__(self):
        return u"{} [{}]".format(self.event_type, self.notification_user_id)
