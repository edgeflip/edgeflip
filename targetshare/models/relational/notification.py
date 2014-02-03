from django.db import models


class Notification(models.Model):

    notification_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    client_content = models.ForeignKey('ClientContent')
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'notifications'


class NotificationUser(models.Model):

    notification_user_id = models.AutoField(primary_key=True)
    notification = models.ForeignKey('Notification',
                                     related_name='notificationusers')
    uuid = models.CharField(max_length=128, db_index=True)
    fbid = models.BigIntegerField()
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
