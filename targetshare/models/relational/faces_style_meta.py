from django.db import models


class FacesStyleMeta(models.Model):

    faces_style_meta_id = models.AutoField(primary_key=True)
    faces_style = models.ForeignKey('FacesStyle')
    name = models.CharField(max_length=128)
    value = models.CharField(max_length=1024)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'faces_style_meta'
