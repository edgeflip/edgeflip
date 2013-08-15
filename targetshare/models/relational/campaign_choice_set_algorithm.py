from django.db import models


class CampaignChoiceSetAlgorithm(models.Model):

    campaign_choice_set_algorithm_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign', null=True, blank=True)
    choice_set_algorithm = models.ForeignKey(
        'ChoiceSetAlgorithm',
        db_column='choice_set_algoritm_id',
        null=True,
        blank=True
    )
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9,
                                   null=True, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_choice_set_algoritm'
