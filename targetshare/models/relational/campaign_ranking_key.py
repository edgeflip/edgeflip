from django.db import models

from . import manager


class CampaignRankingKey(models.Model):

    campaign_ranking_key_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign', null=True, blank=True,
                                 related_name='campaignrankingkeys')
    ranking_key = models.ForeignKey('RankingKey', null=True, blank=True,
                                    related_name='campaignrankingkeys')
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    objects = manager.TransitoryObjectManager.make()

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_ranking_keys'
        ordering = ('start_dt',)
