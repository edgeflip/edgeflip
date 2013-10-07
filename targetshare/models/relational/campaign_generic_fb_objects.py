from django.db import models

from . import manager


class CampaignGenericFBObjects(models.Model):

    campaign_generic_fb_object_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign', null=True, blank=True,
                                 related_name='campaigngenericfbobjects')
    fb_object = models.ForeignKey('FBObject', null=True, blank=True)
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9,
                                   null=True, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    objects = manager.AssignedObjectManager.make(fb_object)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_generic_fb_objects'
