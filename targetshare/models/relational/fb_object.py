from django.db import models


class FBObject(models.Model):

    fb_object_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', null=True, blank=True, related_name='fbobjects')
    name = models.CharField(max_length=256, blank=True)
    description = models.CharField(max_length=1024, blank=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'fb_objects'
        ordering = ('-create_dt',)
