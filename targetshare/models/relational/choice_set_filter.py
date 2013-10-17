from django.db import models

from . import manager


class ChoiceSetFilter(models.Model):

    choice_set_filter_id = models.AutoField(primary_key=True)
    choice_set = models.ForeignKey('ChoiceSet', related_name='choicesetfilters',
                                   null=True, blank=True)
    filter = models.ForeignKey('Filter', null=True, blank=True)
    url_slug = models.CharField(max_length=64, blank=True)
    propensity_model_type = models.CharField(max_length=32, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    objects = manager.AssignedObjectManager.make(assigned_object=filter,
                                                 signature_fields=[filter])

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'choice_set_filters'
