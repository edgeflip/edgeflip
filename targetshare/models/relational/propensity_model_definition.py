from django.db import models


class PropensityModelDefinition(models.Model):

    propensity_model_definition_id = models.AutoField(primary_key=True)
    propensity_model = models.ForeignKey('PropensityModel')
    propensity_model_type = models.CharField(max_length=64, null=True)
    model_definition = models.TextField(null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'propensity_model_definitions'
