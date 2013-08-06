from django.db import models

from .manager import start_stop_manager


class ChoiceSetFilter(models.Model):

    choice_set_filter_id = models.AutoField(primary_key=True)
    choice_set = models.ForeignKey('ChoiceSet', related_name='choicesetfilters')
    filter = models.ForeignKey('Filter')
    url_slug = models.CharField(max_length=64)
    propensity_model_type = models.CharField(max_length=32, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    objects = start_stop_manager('filter')

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'choice_set_filters'
