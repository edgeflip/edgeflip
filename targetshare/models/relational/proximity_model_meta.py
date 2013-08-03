from django.db import models


class ProximityModelMeta(models.Model):

    proximity_model_meta_id = models.AutoField(primary_key=True)
    proximity_model = models.ForeignKey('ProximityModel')
    name = models.CharField(max_length=256, null=True)
    value = models.CharField(max_length=1024, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'proximity_model_meta'
