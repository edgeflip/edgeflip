from django.db import models


class Campaign(models.Model):

    campaign_id = models.IntegerField()
    client_id = models.IntegerField()
    name = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        app_label = 'reporting'
        db_table = 'campaigns'
