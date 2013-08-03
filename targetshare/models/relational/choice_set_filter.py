from django.db import models


class ChoiceSetFilter(models.Model):

    choice_set_filter_id = models.AutoField(primary_key=True)
    choice_set = models.ForeignKey('ChoiceSet')
    filter = models.ForeignKey('Filter')
    url_slug = models.CharField(max_length=64)
    propensity_model_type = models.CharField(max_length=32, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'choice_set_filters'
