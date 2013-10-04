from django.db import models
from django.utils import timezone


class Notification(models.Model):

    notification_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    content = models.ForeignKey('ClientContent')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'notifications'


class NotificationUser(models.Model):

    notification_user_id = models.AutoField(primary_key=True)
    notification = models.ForeignKey('Notification')
    uuid = models.CharField(max_length=128, db_index=True)
    fbid = models.BigIntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'notification_users'

    @property
    def app_id(self):
        return self.campaign.client.fb_app_id

    def __unicode__(self):
        return u"{}".format(self.uuid)


class NotificationAssignment(models.Model):

    notification_assignment_id = models.AutoField(primary_key=True)
    notification_user = models.ForeignKey(
        'NotificationUser', related_name='assignments')
    campaign = models.ForeignKey('Campaign', null=True, blank=True)
    content = models.ForeignKey('ClientContent', null=True, blank=True)
    feature_type = models.CharField(max_length=128, blank=True)
    feature_row = models.IntegerField(null=True, blank=True)
    random_assign = models.NullBooleanField()
    assign_dt = models.DateTimeField(auto_now_add=True)
    chosen_from_table = models.CharField(max_length=128, blank=True)
    chosen_from_rows = models.CharField(max_length=128, blank=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'notification_assignments'


class NotificationEvent(models.Model):

    notification_event_id = models.AutoField(primary_key=True)
    notification_user = models.ForeignKey(
        'NotificationUser', related_name='events')
    event_type = models.CharField(max_length=64, db_column='type')
    campaign = models.ForeignKey('Campaign', null=True)
    client_content = models.ForeignKey('ClientContent', db_column='content_id', null=True)
    content = models.CharField(max_length=128, blank=True)
    friend_fbid = models.BigIntegerField(null=True, blank=True)
    activity_id = models.BigIntegerField(null=True, blank=True)
    event_datetime = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'notification_events'

    def __unicode__(self):
        return u"{} [{}]".format(self.event_type, self.notification_id)
