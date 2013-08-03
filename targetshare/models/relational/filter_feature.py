from django.db import models


class FilterFeature(models.Model):

    filter_feature_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter')
    feature = models.CharField(max_length=64)
    operator = models.CharField(max_length=32)
    value = models.CharField(max_length=1024)
    value_type = models.CharField(max_length=32)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_features'
