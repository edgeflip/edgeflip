from django.db import models


class Visit(models.Model):

    visit_id = models.AutoField(primary_key=True)
    session_id = models.CharField(db_index=True, max_length=40)
    app_id = models.BigIntegerField(db_column='appid')
    ip = models.GenericIPAddressField()
    fbid = models.BigIntegerField(null=True, blank=True)
    source = models.CharField(blank=True, default='', db_index=True, max_length=256)
    updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'visits'
        unique_together = ('session_id', 'app_id')