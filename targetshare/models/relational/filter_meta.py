from django.db import models


class FilterMeta(models.Model):

    filter_meta_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter')
    name = models.CharField(max_length=128)
    value = models.CharField(max_length=1024)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'filter_meta'
