from django.db import models

from .manager import AssignedFBObjectManager


class CampaignFBObject(models.Model):

    campaign_fb_object_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign', null=True, blank=True,
                                 related_name='campaignfbobjects')
    filter = models.ForeignKey('Filter', null=True, blank=True)
    fb_object = models.ForeignKey('FBObject', null=True, blank=True,
                                  related_name='campaignfbobjects')
    rand_cdf = models.DecimalField(null=True, max_digits=10,
                                   decimal_places=9, blank=True)
    source_url = models.URLField(blank=True, null=True)
    sourced = models.DateTimeField(blank=True, editable=False, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    objects = AssignedFBObjectManager()

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_fb_objects'
        unique_together = ('campaign', 'source_url')
