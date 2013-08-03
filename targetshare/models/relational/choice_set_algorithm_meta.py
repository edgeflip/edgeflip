from django.db import models


class ChoiceSetAlgorithmMeta(models.Model):

    choice_set_algorithm_meta_id = models.AutoField(
        db_column='choice_set_algoritm_meta_id',
        primary_key=True
    )
    choice_set_algorithm = models.ForeignKey(
        'ChoiceSetAlgorithm',
        db_column='choice_set_algoritm_id'
    )
    name = models.CharField(max_length=256, null=True)
    value = models.CharField(max_length=1024, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'choice_set_algoritm_meta'
