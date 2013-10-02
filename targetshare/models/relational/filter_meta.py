from django.db import models

from . import manager


class FilterMeta(models.Model):

    filter_meta_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter', null=True, blank=True)
    name = models.CharField(max_length=128, blank=True)
    value = models.CharField(max_length=1024, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    objects = manager.TransitoryObjectManager.make(signature_fields=[name])

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_meta'
