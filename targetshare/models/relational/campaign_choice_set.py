from django.db import models


class CampaignChoiceSet(models.Model):

    campaign_choice_set_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    choice_set = models.ForeignKey('ChoiceSet')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    allow_generic = models.NullBooleanField()
    generic_url_slug = models.CharField(max_length=64, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_choice_sets'
