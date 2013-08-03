from django.db import models


class CampaignFBObjects(models.Model):

    campaign_fb_object_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    filter = models.ForeignKey('Filter')
    fb_object = models.ForeignKey('FBObject')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_fb_objects'
