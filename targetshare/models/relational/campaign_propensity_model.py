from django.db import models


class CampaignPropensityModel(models.Model):

    campaign_propensity_model_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    propensity_model = models.ForeignKey('PropensityModel')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_propensity_models'
