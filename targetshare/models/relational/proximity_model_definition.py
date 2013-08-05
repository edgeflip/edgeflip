from django.db import models


class ProximityModelDefinition(models.Model):

    proximity_model_definition_id = models.AutoField(primary_key=True)
    proximity_model = models.ForeignKey('ProximityModel', null=True)
    model_definition = models.TextField(blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'proximity_model_definitions'
