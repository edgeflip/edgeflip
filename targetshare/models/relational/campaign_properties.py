import urllib

from django.db import models
from django.core.urlresolvers import reverse

from targetshare import utils
from . import manager


class CampaignProperties(models.Model):

    campaign_property_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign', null=True,
                                 related_name='campaignproperties')
    client_faces_url = models.CharField(max_length=2096)
    client_thanks_url = models.CharField(max_length=2096)
    client_error_url = models.CharField(max_length=2096)
    fallback_campaign = models.ForeignKey(
        'Campaign',
        related_name='fallbackcampaign_properties',
        null=True
    )
    fallback_content = models.ForeignKey('ClientContent', null=True)
    fallback_is_cascading = models.NullBooleanField()
    min_friends = models.IntegerField(default=1)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    objects = manager.TransitoryObjectManager.make()

    def faces_url(self, content_id):
        url = self.client_faces_url
        url += '&' if '?' in url else '?'
        slug = utils.encodeDES('%s/%s' % (self.campaign_id, content_id))
        return url + 'efcmpgslug=' + str(slug)

    def incoming_redirect(self, is_secure, host, content_id):
        return urllib.quote_plus('{}{}{}'.format(
            'https://' if is_secure else 'http://',
            host,
            reverse('incoming-encoded', args=[utils.encodeDES('%s/%s' % (
                self.campaign.pk, content_id))])
        ))

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_properties'
