from django.db import models


class ShareMessage(models.Model):

    activity_id = models.BigIntegerField(primary_key=True, default=0)
    fbid = models.BigIntegerField()
    campaign = models.ForeignKey('Campaign')
    content = models.ForeignKey('ClientContent')
    message = models.TextField(null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'share_messages'
