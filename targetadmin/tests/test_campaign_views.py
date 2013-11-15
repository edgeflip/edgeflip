from django.core.urlresolvers import reverse

from . import TestAdminBase
from targetshare.models import relational


class TestCampaignViews(TestAdminBase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestCampaignViews, self).setUp()
        self.campaign = self.test_client.campaigns.get(pk=1)

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
                'generic_fb_object': fb_obj.pk,
                'fb_object': fb_obj.pk
            }
        )
        self.assertStatusCode(response, 302)
        campaign = relational.Campaign.objects.get(name='Test Campaign Creation')
        self.assertRedirects(
            response,
            reverse('campaign-detail', args=[self.test_client.pk, campaign.pk])
        )
        properties = campaign.campaignproperties.get()
        self.assertEqual(properties.client_faces_url, 'http://test.com/faces/')

        cs = campaign.campaignchoicesets.get()
        self.assertEqual(cs.choice_set, choice_set)

        global_filter = campaign.campaignglobalfilters.get()
        self.assertEqual(global_filter.filter, filter_obj)

        campaign_style = campaign.campaignbuttonstyles.get()
        self.assertEqual(campaign_style.button_style, button_style)

        fb_objs = campaign.campaignfbobjects.all()
        self.assertEqual(fb_objs.count(), 1)

        assert campaign.campaigngenericfbobjects.exists()

    def test_campaign_creation_without_generic_fb_obj(self):
        ''' Test creating a campaign without specifying a generic FB object '''
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
                'allow_generic': False,
                'generic_url_slug': 'testing',
                'fb_object': fb_obj.pk
            }
        )
        self.assertStatusCode(response, 302)
        campaign = relational.Campaign.objects.get(name='Test Campaign Creation')
        self.assertRedirects(
            response,
            reverse('campaign-detail', args=[self.test_client.pk, campaign.pk])
        )
        properties = campaign.campaignproperties.get()
        self.assertEqual(properties.client_faces_url, 'http://test.com/faces/')

        cs = campaign.campaignchoicesets.get()
        self.assertEqual(cs.choice_set, choice_set)

        global_filter = campaign.campaignglobalfilters.get()
        self.assertEqual(global_filter.filter, filter_obj)

        campaign_style = campaign.campaignbuttonstyles.get()
        self.assertEqual(campaign_style.button_style, button_style)

        fb_objs = campaign.campaignfbobjects.all()
        self.assertEqual(fb_objs.count(), 1)

    def test_campaign_creation_genric_fb_obj_error(self):
        ''' Test creating a campaign without specifying a generic FB object,
        but specifying "allow_generic" as True. Should result in a form
        validation error
        '''
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
                'fb_object': fb_obj.pk
            }
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response.context['form'].errors['generic_fb_object'][0],
            'Generic FB Object not selected, but Allow Generic specified as True'
        )

    def test_campaign_clone(self):
        response = self.client.get(
            reverse('campaign-new', args=[self.test_client.pk]), {
                'clone_pk': 1
            }
        )
        self.assertStatusCode(response, 200)
        props = self.campaign.campaignproperties.get()
        initial_dict = {
            'faces_url': props.client_faces_url,
            'error_url': props.client_error_url,
            'thanks_url': props.client_thanks_url,
            'generic_fb_object': self.campaign.generic_fb_object.fb_object,
            'allow_generic': True,
            'fallback_campaign': None,
            'min_friends_to_show': 1,
            'fb_object': self.campaign.fb_object.fb_object,
            'generic_url_slug': u'all',
            'global_filter': self.campaign.global_filter.filter,
            'button_style': None,
            'cascading_fallback': None,
            'choice_set': self.campaign.choice_set.choice_set,
            'fallback_content': None
        }
        self.assertEqual(
            response.context['form'].initial,
            initial_dict
        )
