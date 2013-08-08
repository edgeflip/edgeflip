from django.db import models


class CampaignGlobalFilter(models.Model):

    campaign_global_filter_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign', null=True, blank=True)
    filter = models.ForeignKey('Filter', null=True, blank=True)
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9,
                                   null=True, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_global_filters'