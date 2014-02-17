from django.core.exceptions import ImproperlyConfigured
from targetshare.models.relational import Campaign

from .. import EdgeFlipTestCase


class TestCampaignProperties(EdgeFlipTestCase):

    def _create_campaign(self, campaign_name, fallback_campaign_obj=None):
        campaign = Campaign.objects.create(
            name=campaign_name, 
        )
        campaign.campaignproperties.create(
            fallback_campaign=fallback_campaign_obj,
        )
        return campaign

    def test_save(self):
        ''' Test creating a campaign with fallbacks and ensuring the roots show up correctly'''
        fallest_back = self._create_campaign('Fallest back', None)
        faller_back = self._create_campaign('Faller back', fallest_back)
        fall_back = self._create_campaign('Fall back', faller_back)
        real = self._create_campaign('Real', fall_back)

        for campaign in [fallest_back, faller_back, fall_back, real]:
            self.assertEquals(
                campaign.campaignproperties.get().root_campaign,
                real
            )
    def test_save_nofallback(self):
        campaign = self._create_campaign('Test', None)
        self.assertEquals(
            campaign.campaignproperties.get().root_campaign,
            campaign
        )

    def test_save_shenanigans(self):
        with self.assertRaises(ImproperlyConfigured):
            one = self._create_campaign("This is the song that doesn't end", None)
            two = self._create_campaign("It just goes on and on my friend", one)
            three = self._create_campaign("Some people started singing it not knowing what it was", two)
            four = self._create_campaign("And they'll continue singing it forever just because", three)
            props = one.campaignproperties.get()
            props.fallback_campaign = four
            props.save()
            
