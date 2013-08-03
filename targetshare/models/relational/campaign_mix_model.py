from django.db import models


class CampaignMixModel(models.Model):

    campaign_mix_model_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    mix_model = models.ForeignKey('MixModel')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_mix_models'
