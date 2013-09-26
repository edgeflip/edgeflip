from django.db import models

from targetshare import utils


class CampaignProperties(models.Model):

    campaign_property_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign', null=True,
                                 related_name='campaignproperties')
    client_faces_url = models.CharField(max_length=2096)
    client_thanks_url = models.CharField(max_length=2096)
    client_error_url = models.CharField(max_length=2096)
    fallback_campaign = models.ForeignKey(
        'Campaign',
        related_name='fallback_campaign',
        null=True
    )
    fallback_content = models.ForeignKey('ClientContent', null=True)
    fallback_is_cascading = models.NullBooleanField()
    min_friends = models.IntegerField(default=1)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def faces_url(self, content_id):
        url = self.client_faces_url
        if (url.find('?') == -1):
            url += '?'
        else:
            url += '&'

        slug = utils.encodeDES('%s/%s' % (self.campaign_id, content_id))

        return url + 'efcmpgslug=' + str(slug)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_properties'
