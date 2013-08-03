from django.db import models


class MixModelDefinition(models.Model):

    mix_model_definition_id = models.AutoField(primary_key=True)
    mix_model = models.ForeignKey('MixModel')
    model_definition = models.TextField(null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'mix_model_definitions'
