from django.db import models

class Campchain(models.Model):
    root_id = models.IntegerField()
    parent_id = models.IntegerField()
    child_id = models.IntegerField(null=True)

    class Meta(object):
        app_label = 'reporting'
        db_table = 'campchain'
