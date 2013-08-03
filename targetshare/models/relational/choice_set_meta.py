from django.db import models


class ChoiceSetMeta(models.Model):

    choice_set_meta_id = models.AutoField(primary_key=True)
    choice_set = models.ForeignKey('ChoiceSet')
    name = models.CharField(max_length=256, null=True)
    value = models.CharField(max_length=1024, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'choice_set_meta'
