from django.db import models


class ChoiceSetAlgorithm(models.Model):

    choice_set_algorithm_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'choice_set_algoritms'
