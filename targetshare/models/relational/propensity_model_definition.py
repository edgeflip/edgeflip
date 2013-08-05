from django.db import models


class PropensityModelDefinition(models.Model):

    propensity_model_definition_id = models.AutoField(primary_key=True)
    propensity_model = models.ForeignKey('PropensityModel',
                                         null=True, blank=True)
    propensity_model_type = models.CharField(max_length=64, blank=True)
    model_definition = models.TextField(blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'propensity_model_definitions'
