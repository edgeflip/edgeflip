from django.db import models


class CampaignMeta(models.Model):

    campaign_meta_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    name = models.CharField(max_length=256)
    value = models.TextField(blank=True, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'campaign_meta'
