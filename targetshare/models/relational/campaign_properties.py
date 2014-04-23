from django.core.exceptions import ImproperlyConfigured
from django.db import models
import logging

from targetshare import utils
from . import manager

LOG = logging.getLogger('crow')

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
    num_faces = models.PositiveIntegerField(default=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)
    root_campaign = models.ForeignKey(
        'Campaign',
        related_name='rootcampaign_properties',
        null=True,
    )

    objects = manager.TransitoryObjectManager.make()


    def __init__(self, *args, **kws):
        super(CampaignProperties, self).__init__(*args, **kws)
        self._original = {'campaign': None, 'fallback_campaign': None}
        if self.campaign_property_id:
            # Assume retrieved from DB
            self._original.update(campaign=self.campaign, fallback_campaign=self.fallback_campaign)


    def faces_url(self, content_id):
        url = self.client_faces_url
        url += '&' if '?' in url else '?'
        slug = utils.encodeDES('%s/%s' % (self.campaign_id, content_id))
        return url + 'efcmpgslug=' + str(slug)

    def _calculate_root_campaign(self):
        root_campaign = None
        current_campaign = self
        seen_campaign_ids = set()
        while root_campaign is None:
            parents = current_campaign.parent()
            if len(parents) == 0:
                root_campaign = current_campaign
            elif len(parents) > 1:
                raise ImproperlyConfigured(
                    'Multiple campaign roots detected traversing forward at campaign_id {0}'
                    .format(current_campaign.campaign_id)
                )
            elif parents[0].campaign_id in seen_campaign_ids:
                raise ImproperlyConfigured(
                    'Fallback loop detected traversing forward at campaign_id {0}'
                    .format(parents[0].campaign_id)
                )
            else:
                current_campaign = parents[0]
                seen_campaign_ids.add(current_campaign.campaign_id)

        return root_campaign.campaign


    @staticmethod
    def _traverse(start, root):
        current = start
        seen_campaign_ids = set()
        while current is not None:
            if current.campaign_id in seen_campaign_ids:
                raise ImproperlyConfigured(
                    'Fallback loop detected traversing backward at campaign_id {0}'
                    .format(current.campaign_id)
                )
            seen_campaign_ids.add(current.campaign_id)
            current.campaignproperties.update(root_campaign=root)
            current = current.campaignproperties.get().fallback_campaign


    def parent(self):
        return self._default_manager.filter(fallback_campaign_id=self.campaign_id)

    @property
    def is_root(self):
        return not self.parent().exists()

    def save(self, *args, **kws):
        if self.root_campaign is None and self.is_root:
            self.root_campaign = self.campaign

        result = super(CampaignProperties, self).save(*args, **kws)

        if self.fallback_campaign != self._original['fallback_campaign']:
            try:
                self._traverse(self.fallback_campaign, self._calculate_root_campaign())
                # fix orphan nodes
                self._traverse(self._original['fallback_campaign'], None)
                self._original.update(fallback_campaign=self.fallback_campaign)
            except ImproperlyConfigured as e:
                LOG.exception(
                    "Could not save root campaign with campaign_id %s. Reason? %s",
                    self.campaign.campaign_id,
                    str(e)
                )

        return result


    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_properties'
