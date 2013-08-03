from django.db import models


class FBObjectMeta(models.Model):

    fb_object_meta_id = models.AutoField(primary_key=True)
    fb_object = models.ForeignKey('FBObject')
    name = models.CharField(max_length=128)
    value = models.CharField(max_length=1024)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'fb_object_meta'
