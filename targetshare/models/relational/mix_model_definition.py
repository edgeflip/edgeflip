from django.db import models


class MixModelDefinition(models.Model):

    mix_model_definition_id = models.AutoField(primary_key=True)
    mix_model = models.ForeignKey('MixModel', null=True, blank=True)
    model_definition = models.TextField(blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'mix_model_definitions'
