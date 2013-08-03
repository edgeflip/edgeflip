from django.db import models


class ProximityModelDefinition(models.Model):

    proximity_model_definition_id = models.AutoField(primary_key=True)
    proximity_model = models.ForeignKey('ProximityModel')
    model_definition = models.TextField(null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'proximity_model_definitions'
