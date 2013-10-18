from django.db import models

from . import manager


class Visit(models.Model):

    visit_id = models.AutoField(primary_key=True)
    visitor = models.ForeignKey('targetshare.Visitor')
    session_id = models.CharField(db_index=True, max_length=40)
    app_id = models.BigIntegerField(db_column='appid')
    ip = models.GenericIPAddressField()
    source = models.CharField(blank=True, default='', db_index=True, max_length=256)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = manager.Manager()

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'visits'
        unique_together = ('session_id', 'app_id')

    def __unicode__(self):
        return u"{} [{}]".format(self.session_id, self.app_id)
