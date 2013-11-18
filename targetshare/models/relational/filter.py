import logging

from django.db import models


logger = logging.getLogger(__name__)


class Filter(models.Model):

    filter_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', related_name='filters',
                               null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    description = models.CharField(max_length=1024, blank=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filters'
        ordering = ('-create_dt',)
