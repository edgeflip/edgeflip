from django.core.urlresolvers import reverse

from . import TestAdminBase
from targetshare.models import relational


class TestCampaignViews(TestAdminBase):

    fixtures = ['targetadmin_test_data']

    def setUp(self):
        super(TestCampaignViews, self).setUp()
        self.campaign = self.test_client.campaign_set.create(
            name='test campaign')

    def test_campaign_list_view(self):
        ''' Test viewing a content list '''
        response = self.client.get(
            reverse('campaign-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_campaign_detail_view(self):
        ''' Test viewing a content object '''
        response = self.client.get(
            reverse('campaign-detail', args=[self.test_client.pk, self.campaign.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object']

    def test_campaign_creation(self):
        ''' Test creating a campaign '''
        filter_obj = relational.Filter.objects.create(
            client=self.test_client, name='test filter')
        choice_set = relational.ChoiceSet.objects.create(
            client=self.test_client, name='test cs')
        button_style = relational.ButtonStyle.objects.create(
            client=self.test_client, name='test button')
        fb_obj = relational.FBObject.objects.create(
            client=self.test_client, name='test fbobj')
        response = self.client.post(
            reverse('campaign-new', args=[self.test_client.pk]), {
                'name': 'Test Campaign Creation',
                'description': 'Test Description',
                'faces_url': 'http://test.com/faces/',
                'thanks_url': 'http://test.com/thanks/',
                'error_url': 'http://test.com/error/',
                'cascading_fallback': False,
                'min_friends_to_show': 1,
                'global_filter': filter_obj.pk,
                'button_style': button_style.pk,
                'choice_set': choice_set.pk,
                'allow_generic': True,
                'generic_url_slug': 'testing',
                'fb_object': fb_obj.pk,
                'fb_object_two': fb_obj.pk
            }
        )
        campaign = relational.Campaign.objects.get(name='Test Campaign Creation')
        self.assertRedirects(
            response,
            reverse('campaign-detail', args=[self.test_client.pk, campaign.pk])
        )
        properties = campaign.campaignproperties_set.get()
        self.assertEqual(properties.client_faces_url, 'http://test.com/faces/')

        cs = campaign.campaignchoiceset_set.get()
        self.assertEqual(cs.choice_set, choice_set)

        global_filter = campaign.campaignglobalfilter_set.get()
        self.assertEqual(global_filter.filter, filter_obj)

        campaign_style = campaign.campaignbuttonstyle_set.get()
        self.assertEqual(campaign_style.button_style, button_style)

        fb_objs = campaign.campaignfbobjects_set.all()
        for x in fb_objs:
            self.assertEqual(x.fb_object, fb_obj)
