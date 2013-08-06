from django.db import models


class ClientDefault(models.Model):

    client_default_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', related_name='clientdefaults')
    button_style = models.ForeignKey('ButtonStyle', null=True)
    faces_style = models.ForeignKey('FacesStyle', null=True)
    propensity_model = models.ForeignKey('PropensityModel', null=True)
    proximity_model = models.ForeignKey('ProximityModel', null=True)
    mix_model = models.ForeignKey('MixModel', null=True)
    filter = models.ForeignKey('Filter', null=True)
    choice_set = models.ForeignKey('ChoiceSet', null=True)
    choice_set_algorithm = models.ForeignKey('ChoiceSetAlgorithm', null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'client_defaults'
