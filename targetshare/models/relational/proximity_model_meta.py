from django.db import models


class ProximityModelMeta(models.Model):

    proximity_model_meta_id = models.AutoField(primary_key=True)
    proximity_model = models.ForeignKey('ProximityModel', null=True, blank=True)
    name = models.CharField(max_length=256, blank=True)
    value = models.CharField(max_length=1024, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'proximity_model_meta'
