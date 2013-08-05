from django.db import models


class MixModelMeta(models.Model):

    mix_model_meta_id = models.AutoField(primary_key=True)
    mix_model = models.ForeignKey('MixModel', null=True, blank=True)
    name = models.CharField(max_length=256, blank=True)
    value = models.CharField(max_length=1024, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'mix_model_meta'
