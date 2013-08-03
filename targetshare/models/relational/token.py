import datetime

from django.db import models


class Token(models.Model):

    fbid = models.BigIntegerField(primary_key=True)
    app_id = models.BigIntegerField(db_column='appid')
    owner_id = models.BigIntegerField(db_column='ownerid')
    token = models.CharField(max_length=512)
    expires = models.DateTimeField(null=True)
    updated = models.DateTimeField(auto_now=True, default=datetime.datetime.now) # FIXME: default?

    class Meta(object):
        app_label = 'targetshare'
        unique_together = ('fbid', 'app_id', 'owner_id')
        db_table = 'tokens'
