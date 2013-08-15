from django.db import models


class Assignment(models.Model):

    assignment_id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=128, blank=True)
    campaign = models.ForeignKey('Campaign', null=True, blank=True)
    content = models.ForeignKey('ClientContent', null=True, blank=True)
    feature_type = models.CharField(max_length=128, blank=True)
    feature_row = models.IntegerField(null=True, blank=True)
    random_assign = models.NullBooleanField()
    assign_dt = models.DateTimeField(auto_now_add=True)
    chosen_from_table = models.CharField(max_length=128, blank=True)
    chosen_from_rows = models.CharField(max_length=128, blank=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'assignments'
