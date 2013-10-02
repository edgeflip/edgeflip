from django.db import models

from . import manager


class CampaignFacesStyle(models.Model):

    campaign_faces_style_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign', null=True, blank=True,
                                 related_name='campaignfacesstyles')
    faces_style = models.ForeignKey('FacesStyle', null=True, blank=True)
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9,
                                   null=True, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    objects = manager.AssignedObjectManager.make(faces_style)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_faces_styles'
