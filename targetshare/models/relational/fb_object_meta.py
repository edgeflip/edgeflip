from django.db import models


class FBObjectMeta(models.Model):

    fb_object_meta_id = models.AutoField(primary_key=True)
    fb_object = models.ForeignKey('FBObject', null=True)
    name = models.CharField(max_length=128, blank=True)
    value = models.CharField(max_length=1024, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'fb_object_meta'
