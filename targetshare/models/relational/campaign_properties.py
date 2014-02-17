from django.core.exceptions import ImproperlyConfigured
from django.db import models

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
    root_campaign = models.ForeignKey(
        'Campaign',
        related_name='rootcampaign_properties',
        null=True,
        db_index=True
    )

    objects = manager.TransitoryObjectManager.make()

    def faces_url(self, content_id):
        url = self.client_faces_url
        url += '&' if '?' in url else '?'
        slug = utils.encodeDES('%s/%s' % (self.campaign_id, content_id))
        return url + 'efcmpgslug=' + str(slug)


    def save(self, *args, **kws):
        if kws.has_key('root_campaign_override'):
            self.root_campaign = kws['root_campaign_override']
            del kws['root_campaign_override']
            return super(CampaignProperties, self).save(*args, **kws)
        else:
            # set root campaign for me and all my friends
            self.root_campaign = self.campaign
            return_value = super(CampaignProperties, self).save(*args, **kws)
            seen_campaign_ids = set()
            get_fallback = lambda camp: camp.campaignproperties.get().fallback_campaign
            fallback = get_fallback(self.campaign)
            seen_campaign_ids.add(self.campaign_id)
            while fallback is not None:
                if fallback.campaign_id in seen_campaign_ids:
                    raise ImproperlyConfigured('Fallback loop detected')
                seen_campaign_ids.add(fallback.campaign_id)
                fallback.campaignproperties.get().save(root_campaign_override=self.campaign)
                fallback = get_fallback(fallback)
            return return_value

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_properties'
