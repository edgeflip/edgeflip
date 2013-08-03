from django.db import models


class PropensityModel(models.Model):

    proximity_model_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True)
    description = models.CharField(max_length=1024, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'propensity_models'
