from django.db import models


class ClientDefault(models.Model):

    client_default_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', null=True, blank=True)
    button_style = models.ForeignKey('ButtonStyle', null=True, blank=True)
    faces_style = models.ForeignKey('FacesStyle', null=True, blank=True)
    propensity_model = models.ForeignKey('PropensityModel', null=True,
                                         blank=True)
    proximity_model = models.ForeignKey('ProximityModel', null=True, blank=True)
    mix_model = models.ForeignKey('MixModel', null=True, blank=True)
    filter = models.ForeignKey('Filter', null=True, blank=True)
    choice_set = models.ForeignKey('ChoiceSet', null=True, blank=True)
    choice_set_algorithm = models.ForeignKey('ChoiceSetAlgorithm',
                                             null=True, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'client_defaults'
