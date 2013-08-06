from django.db import models

from .manager import start_stop_manager


class FilterMeta(models.Model):

    filter_meta_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter')
    name = models.CharField(max_length=128)
    value = models.CharField(max_length=1024)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    objects = start_stop_manager('name')

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_meta'
