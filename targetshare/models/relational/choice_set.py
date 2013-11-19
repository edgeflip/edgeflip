from django.db import models


class ChoiceSet(models.Model):

    choice_set_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', related_name='choicesets',
                               null=True, blank=True)
    name = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'choice_sets'
        ordering = ('-create_dt',)
