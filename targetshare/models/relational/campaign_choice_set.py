from django.db import models


class CampaignChoiceSet(models.Model):

    campaign_choice_set_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign', null=True)
    choice_set = models.ForeignKey('ChoiceSet', null=True)
    rand_cdf = models.DecimalField(null=True, max_digits=10,
                                   decimal_places=9, blank=True)
    allow_generic = models.NullBooleanField()
    generic_url_slug = models.CharField(max_length=64, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_choice_sets'
