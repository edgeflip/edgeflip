from django.db import models


class FilterFeature(models.Model):

    filter_feature_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter', null=True)
    feature = models.CharField(max_length=64, blank=True)
    operator = models.CharField(max_length=32, blank=True)
    value = models.CharField(max_length=1024, blank=True)
    value_type = models.CharField(max_length=32, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_features'
