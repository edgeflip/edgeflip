from django.db import models


class CampaignFacesStyle(models.Model):

    campaign_faces_style_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    faces_style = models.ForeignKey('FacesStyle')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_faces_styles'
