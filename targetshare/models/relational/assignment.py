from django.db import models


class Assignment(models.Model):

    assignment_id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=128)
    campaign = models.ForeignKey('Campaign')
    content = models.ForeignKey('ClientContent')
    feature_type = models.CharField(max_length=128)
    feature_row = models.IntegerField()
    random_assign = models.BooleanField(default=False)
    assign_dt = models.DateTimeField(auto_now_add=True)
    chosen_from_table = models.CharField(max_length=128)
    chosen_from_rows = models.CharField(max_length=128)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'assignments'
