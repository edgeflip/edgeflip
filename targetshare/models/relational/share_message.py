from django.db import models


class ShareMessage(models.Model):

    activity_id = models.BigIntegerField(primary_key=True)
    fbid = models.BigIntegerField(null=True, blank=True)
    campaign = models.ForeignKey('Campaign', null=True, blank=True,)
    content = models.ForeignKey('ClientContent', null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'share_messages'
