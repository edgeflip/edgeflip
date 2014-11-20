from targetshare.models.relational import Campaign, ClientContent
from mock import patch

from .. import EdgeFlipTestCase


class TestCampaignProperties(EdgeFlipTestCase):

    def _create_campaign(self, campaign_name, fallback_campaign_obj=None):
        campaign = Campaign.objects.create(name=campaign_name)
        content = ClientContent.objects.create()
        campaign.campaignproperties.create(fallback_campaign=fallback_campaign_obj,
                                           client_content=content)
        return campaign

    def test_parent(self):
        one = self._create_campaign('One', None)
        two = self._create_campaign('Two', one)

        self.assertEquals(one.campaignproperties.get().parent().get().campaign, two)
        self.assertFalse(two.campaignproperties.get().parent().exists())

    def test_is_root(self):
        one = self._create_campaign('One', None)
        two = self._create_campaign('Two', one)

        self.assertFalse(one.campaignproperties.get().is_root)
        self.assertTrue(two.campaignproperties.get().is_root)

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

    @patch('targetshare.models.relational.campaign_properties.LOG')
    def test_save_shenanigans(self, logger_mock):
        # make sure we don't infinitely recurse if somebody
        # manages to make a campaign loop, but do save the model
        # and log the error
        one = self._create_campaign("This is the song that doesn't end", None)
        two = self._create_campaign("It just goes on and on my friend", one)
        three = self._create_campaign("Some people started singing it not knowing what it was", two)
        four = self._create_campaign("And they'll continue singing it forever just because", three)
        props = one.campaignproperties.get()
        props.fallback_campaign = four
        props.save()
        self.assertEquals(
            one.campaignproperties.get().fallback_campaign,
            four
        )
        self.assertIn('Could not save root campaign', logger_mock.exception.call_args[0][0])
        self.assertEquals(
            logger_mock.exception.call_args[0][1],
            one.campaign_id
        )
        self.assertIn('Fallback loop detected', str(logger_mock.exception.call_args[0][2]))

    def test_save_nonroot(self):
        # change something unrelated on a nonroot node and
        # ensure the chain stays intact
        one = self._create_campaign('One', None)
        two = self._create_campaign('Two', one)
        three = self._create_campaign('Three', two)
        props = two.campaignproperties.get()
        props.cascading_fallback = True
        props.save
        for campaign in [one, two, three]:
            self.assertEquals(
                campaign.campaignproperties.get().root_campaign,
                three
            )

    def test_save_orphan(self):
        # cut off a campaign from its chain
        one = self._create_campaign('One', None)
        two = self._create_campaign('Two', one)
        three = self._create_campaign('Three', None)

        # change the fallback to a new one and the old one should lose its root
        props = two.campaignproperties.get()
        props.fallback_campaign = three
        props.save()
        self.assertIsNone(one.campaignproperties.get().root_campaign)
        self.assertEquals(
            three.campaignproperties.get().root_campaign,
            two
        )

        # remove the fallback entirely and nobody should have a root
        props.fallback_campaign = None
        props.save()
        self.assertIsNone(three.campaignproperties.get().root_campaign)

    def test_save_adopt(self):
        # create two campaigns independently and then link them later
        one = self._create_campaign('One', None)
        two = self._create_campaign('Two', None)
        props = one.campaignproperties.get()
        props.fallback_campaign = two
        props.save()

        for campaign in [one, two]:
            self.assertEquals(
                campaign.campaignproperties.get().root_campaign,
                one
            )

    def test_deferred_field_query(self):
        campaign = self._create_campaign('Test')
        props = campaign.campaignproperties.only('num_faces').get()
        self.assertEqual(props.num_faces, 10)
