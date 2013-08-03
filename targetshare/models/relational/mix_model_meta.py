from django.db import models


class MixModelMeta(models.Model):

    mix_model_meta_id = models.AutoField(primary_key=True)
    mix_model = models.ForeignKey('MixModel')
    name = models.CharField(max_length=256, null=True)
    value = models.CharField(max_length=1024, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'mix_model_meta'
