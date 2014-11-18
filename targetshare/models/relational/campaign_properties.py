import logging

from django.core.exceptions import ImproperlyConfigured
from django.db import models

from . import manager

LOG = logging.getLogger('crow')


class CampaignProperties(models.Model):

    class Status(object):
        DRAFT = 'draft'
        PUBLISHED = 'published'
        INACTIVE = 'inactive'
        CHOICES = (
            (DRAFT, 'Draft'),
            (PUBLISHED, 'Published'),
            (INACTIVE, 'Inactive')
        )

    campaign_property_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign', null=True,
                                 related_name='campaignproperties')
    client_content = models.ForeignKey('ClientContent',
                                       db_column='content_id',
                                       related_name='campaignproperties',
                                       help_text="Default client content to pair with the campaign")
    client_faces_url = models.CharField(max_length=2096)
    client_thanks_url = models.CharField(max_length=2096)
    client_error_url = models.CharField(max_length=2096)
    fallback_campaign = models.ForeignKey('Campaign', null=True,
                                          related_name='fallbackcampaign_properties')
    fallback_content = models.ForeignKey('ClientContent', null=True,
                                         related_name='fallbackcampaign_properties')
    fallback_is_cascading = models.NullBooleanField()
    root_campaign = models.ForeignKey('Campaign', null=True,
                                      related_name='rootcampaign_properties')
    min_friends = models.IntegerField(default=1)
    num_faces = models.PositiveIntegerField(default=10)
    status = models.CharField(max_length=32, default=Status.DRAFT, choices=Status.CHOICES)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    objects = manager.TransitoryObjectManager.make()

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
        original_fallback = None
        if self.pk:
            try:
                original = self._default_manager.only('fallback_campaign').get(pk=self.pk)
            except self.DoesNotExist:
                # Primary key must have been provided to new instance
                pass
            else:
                original_fallback = original.fallback_campaign

        if self.root_campaign is None and self.is_root:
            self.root_campaign = self.campaign

        result = super(CampaignProperties, self).save(*args, **kws)

        if self.fallback_campaign != original_fallback:
            try:
                self._traverse(self.fallback_campaign, self._calculate_root_campaign())
                self._traverse(original_fallback, None) # fix orphan nodes
            except ImproperlyConfigured as exc:
                LOG.exception("Could not save root campaign with campaign_id %s. Reason? %s",
                              self.campaign.campaign_id, exc)

        return result

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaign_properties'
