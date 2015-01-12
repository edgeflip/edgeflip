from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.query import QuerySet


class CampaignQuerySetBase(QuerySet):

    def _rootonly(self):
        return self.filter(campaignproperties__root_campaign_id=models.F('campaign_id'))


class CampaignQuerySet(CampaignQuerySetBase):

    def root(self):
        return self._rootonly()


class CampaignManager(models.Manager):
    """Campaign object manager

    Contributes the campaign-specific method `root()`, which filters the
    QuerySet to root campaigns, and returns a QuerySet which also provides this
    method.

    """
    def get_queryset(self):
        return CampaignQuerySet(self.model, using=self._db)

    def root(self):
        return self.get_queryset().root()


class RootCampaignManager(models.Manager):
    """Alternative campaign object manager whose view is restricted to root
    campaigns.

    """
    def get_queryset(self):
        campaigns = CampaignQuerySetBase(self.model, using=self._db)
        return campaigns._rootonly()


class Campaign(models.Model):

    campaign_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', null=True, blank=True, related_name='campaigns')
    name = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True, blank=True)

    objects = CampaignManager()
    rootcampaigns = RootCampaignManager()

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'campaigns'

    def __unicode__(self):
        return u'%s' % self.name

    # Helpers assuming a basic configuration #

    def status(self):
        status_only_props = self.campaignproperties.only('status').get()
        return status_only_props.status

    def iterfallbacks(self):
        campaign = self
        while True:
            props = campaign.campaignproperties.get()
            campaign = props.fallback_campaign
            if campaign is None:
                break
            yield campaign

    def iterchain(self):
        yield self
        for fallback in self.iterfallbacks():
            yield fallback

    def global_filter(self, dt=None):
        try:
            campaign_global_filter = self.campaignglobalfilters.for_datetime(datetime=dt).get()
        except ObjectDoesNotExist:
            return None
        else:
            return campaign_global_filter.filter

    def campaign_choice_set(self, dt=None):
        try:
            return self.campaignchoicesets.for_datetime(datetime=dt).get()
        except ObjectDoesNotExist:
            return None

    def choice_set(self, dt=None):
        campaign_choice_set = self.campaign_choice_set(dt)
        return campaign_choice_set and campaign_choice_set.choice_set

    def button_style(self, dt=None):
        try:
            campaign_button_style = self.campaignbuttonstyles.for_datetime(datetime=dt).get()
        except ObjectDoesNotExist:
            return None
        else:
            return campaign_button_style.button_style

    def generic_fb_object(self, dt=None):
        try:
            campaign_generic_fb_object = self.campaigngenericfbobjects.for_datetime(datetime=dt).get()
        except ObjectDoesNotExist:
            return None
        else:
            return campaign_generic_fb_object.fb_object

    def fb_object(self, dt=None):
        try:
            campaign_fb_object = self.campaignfbobjects.for_datetime(datetime=dt).get()
        except ObjectDoesNotExist:
            return None
        else:
            return campaign_fb_object.fb_object
