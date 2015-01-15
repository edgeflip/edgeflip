import json
from decimal import Decimal
from itertools import chain

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse

from targetshare.models import relational
from targetshare.views.utils import encodeDES

from . import TestAdminBase


Status = relational.CampaignProperties.Status


class TestCampaignWizard(TestAdminBase):

    fixtures = ['admin_test_data']

    def test_create_campaign_wizard(self):
        new_client = relational.Client.objects.create(
            name='Test Client',
            fb_app_id=1,
        )
        new_filter = relational.Filter.objects.create(
            name='new filter', client=new_client
        )
        relational.FilterFeature.objects.create(
            feature=relational.FilterFeature.Expression.AGE,
            operator=relational.FilterFeature.Operator.MIN,
            value=16, filter=new_filter
        )
        relational.FilterFeature.objects.create(
            feature=relational.FilterFeature.Expression.AGE,
            operator=relational.FilterFeature.Operator.MAX,
            value=60, filter=new_filter
        )
        relational.FilterFeature.objects.create(
            feature=relational.FilterFeature.Expression.STATE,
            operator=relational.FilterFeature.Operator.IN,
            value='Illinois||Missouri', filter=new_filter
        )
        relational.FilterFeature.objects.create(
            feature=relational.FilterFeature.Expression.CITY,
            operator=relational.FilterFeature.Operator.EQ,
            value='Chicago', filter=new_filter
        )
        self.assertEqual(new_client.filters.count(), 1)
        self.assertFalse(new_client.fbobjects.exists())
        self.assertFalse(new_client.choicesets.exists())
        self.assertFalse(new_client.buttonstyles.exists())
        self.assertFalse(new_client.campaigns.exists())
        response = self.client.post(
            reverse('targetadmin:campaign-wizard', args=[new_client.pk]), {
                # Campaign Details
                'name': 'Test Campaign',
                'faces_url': 'http://www.faces.com',
                'error_url': 'http://www.error.com',
                'thanks_url': 'http://www.thanks.com',
                'content_url': 'http://www.content.com',
                'include_empty_fallback': 1,
                'enabled-filters-1': '"age.min.16","age.max.60"',
                'enabled-filters-2': '"state.in.Illinois||Missouri"',
                'enabled-filters-3': '"city.eq.Chicago"',
                # FB Object
                'og_title': 'Test Title',
                'org_name': 'Test Organization',
                'msg1_pre': 'Hey, ',
                'msg1_post': ' How goes it?',
                'msg2_pre': 'Hey 2, ',
                'msg2_post': ' How goes it 2?',
                'og_image': 'http://imgur.com/VsiPr',
                'sharing_prompt': 'SHARE IT',
                'sharing_button': 'Show Your Support',
                'og_description': 'Description of FB stuff'
            }
        )
        self.assertStatusCode(response, 302)
        camp = new_client.campaigns.latest('pk')
        self.assertRedirects(response,
            reverse('targetadmin:campaign-wizard-finish', args=[new_client.pk, camp.pk]))

        content = new_client.clientcontent.latest('pk')
        cs = camp.campaignchoicesets.get().choice_set
        fb_attr = camp.campaignfbobjects.get().fb_object.fbobjectattribute_set.get()
        self.assertEqual(content.url, 'http://www.content.com')
        self.assertIn('Root', cs.name)
        self.assertIn('Root', cs.choicesetfilters.get().filter.name)
        self.assertTrue(new_client.filters.exists())
        self.assertTrue(new_client.fbobjects.exists())
        self.assertTrue(new_client.choicesets.exists())
        self.assertTrue(new_client.buttonstyles.exists())
        self.assertTrue(new_client.campaigns.exists())
        self.assertEqual(new_client.campaigns.count(), 4)
        # 4 filters, plus the one we created earlier
        self.assertEqual(new_client.filters.count(), 5)
        self.assertEqual(new_client.choicesets.count(), 4)
        self.assertEqual(fb_attr.og_action, 'support')
        self.assertEqual(fb_attr.og_type, 'cause')
        # Page Style
        campaign_page_style_sets = camp.campaignpagestylesets.all()
        self.assertEqual(len(campaign_page_style_sets), 2)
        self.assertEqual(
            [campaign_page_style_set.page_style_set.page_styles.count()
             for campaign_page_style_set in campaign_page_style_sets],
            [1, 1]
        )
        page_styles_pages = (
            campaign_page_style_set.page_style_set.page_styles.values_list('page__code', flat=True)
            for campaign_page_style_set in campaign_page_style_sets
        )
        self.assertEqual(
            set(chain.from_iterable(page_styles_pages)),
            {relational.Page.BUTTON, relational.Page.FRAME_FACES}
        )
        (notification,) = mail.outbox
        self.assertIn(camp.name, notification.body)

    def test_create_campaign_wizard_generate_faces_url(self):
        new_client = relational.Client.objects.create(
            name='Test Client',
            fb_app_name='testing',
            fb_app_id=1,
        )
        relational.Filter.objects.update(client=new_client)
        self.assertEqual(new_client.filters.count(), 6)
        self.assertEqual(
            relational.FilterFeature.objects.filter(filter__client=new_client).count(),
            5
        )
        self.assertFalse(new_client.fbobjects.exists())
        self.assertFalse(new_client.choicesets.exists())
        self.assertFalse(new_client.buttonstyles.exists())
        self.assertFalse(new_client.campaigns.exists())
        response = self.client.post(
            reverse('targetadmin:campaign-wizard', args=[new_client.pk]), {
                # Campaign Details
                'name': 'Test Campaign',
                'error_url': 'http://www.error.com',
                'thanks_url': 'http://www.thanks.com',
                'content_url': 'http://www.content.com',
                'include_empty_fallback': 1,
                'enabled-filters-1': '"state.eq.California","full_location.eq.Sacremento, CA United States"',
                # FB Object
                'og_title': 'Test Title',
                'org_name': 'Test Organization',
                'msg1_pre': 'Hey, ',
                'msg1_post': ' How goes it?',
                'msg2_pre': 'Hey 2, ',
                'msg2_post': ' How goes it 2?',
                'og_image': 'http://imgur.com/VsiPr',
                'sharing_prompt': 'SHARE IT',
                'sharing_button': 'Show Your Support',
                'og_description': 'Description of FB stuff'
            }
        )
        self.assertStatusCode(response, 302)
        camp = new_client.campaigns.latest('pk')
        content = new_client.clientcontent.latest('pk')
        cs = camp.campaignchoicesets.get().choice_set
        fb_attr = camp.campaignfbobjects.get().fb_object.fbobjectattribute_set.get()
        self.assertRedirects(response,
            reverse('targetadmin:campaign-wizard-finish', args=[new_client.pk, camp.pk])
        )
        self.assertIn('Root', cs.name)
        self.assertIn('Root', cs.choicesetfilters.get().filter.name)
        self.assertTrue(new_client.filters.exists())
        self.assertTrue(new_client.fbobjects.exists())
        self.assertTrue(new_client.choicesets.exists())
        self.assertTrue(new_client.buttonstyles.exists())
        self.assertTrue(new_client.campaigns.exists())
        self.assertEqual(new_client.campaigns.count(), 2)
        # 1 new one, plus the existing 6
        self.assertEqual(new_client.filters.count(), 7)
        self.assertEqual(
            relational.FilterFeature.objects.filter(filter__client=new_client).count(),
            7
        )
        self.assertEqual(new_client.choicesets.count(), 2)
        self.assertEqual(fb_attr.og_action, 'support')
        self.assertEqual(fb_attr.og_type, 'cause')

        self.assertEqual(
            camp.campaignproperties.get().client_faces_url,
            'https://apps.facebook.com/{}/{}/'.format(
                new_client.fb_app_name,
                encodeDES('{}/{}'.format(camp.pk, content.pk))
            )
        )
        (notification,) = mail.outbox
        self.assertIn(camp.name, notification.body)

    def test_create_campaign_wizard_new_filter_feature(self):
        new_client = relational.Client.objects.create(
            name='Test Client',
            fb_app_name='testing',
            fb_app_id=1,
        )
        self.assertFalse(new_client.filters.exists())
        self.assertFalse(new_client.fbobjects.exists())
        self.assertFalse(new_client.choicesets.exists())
        self.assertFalse(new_client.buttonstyles.exists())
        self.assertFalse(new_client.campaigns.exists())
        self.assertFalse(
            relational.FilterFeature.objects.filter(
                filter__client=new_client).exists()
        )
        response = self.client.post(
            reverse('targetadmin:campaign-wizard', args=[new_client.pk]), {
                # Campaign Details
                'name': 'Test Campaign',
                'error_url': 'http://www.error.com',
                'thanks_url': 'http://www.thanks.com',
                'content_url': 'http://www.content.com',
                'include_empty_fallback': 1,
                'enabled-filters-1': '"state.eq.Kansas","city.eq.Topeka"',
                # FB Object
                'og_title': 'Test Title',
                'org_name': 'Test Organization',
                'msg1_pre': 'Hey, ',
                'msg1_post': ' How goes it?',
                'msg2_pre': 'Hey 2, ',
                'msg2_post': ' How goes it 2?',
                'og_image': 'http://imgur.com/VsiPr',
                'sharing_prompt': 'SHARE IT',
                'sharing_button': 'Show Your Support',
                'og_description': 'Description of FB stuff'
            }
        )
        self.assertStatusCode(response, 302)
        camp = new_client.campaigns.latest('pk')
        content = new_client.clientcontent.latest('pk')
        cs = camp.campaignchoicesets.get().choice_set
        fb_attr = camp.campaignfbobjects.get().fb_object.fbobjectattribute_set.get()
        self.assertRedirects(response,
            reverse('targetadmin:campaign-wizard-finish', args=[new_client.pk, camp.pk])
        )
        self.assertIn('Root', cs.name)
        self.assertIn('Root', cs.choicesetfilters.get().filter.name)
        self.assertTrue(new_client.filters.exists())
        self.assertTrue(new_client.fbobjects.exists())
        self.assertTrue(new_client.choicesets.exists())
        self.assertTrue(new_client.buttonstyles.exists())
        self.assertTrue(new_client.campaigns.exists())
        self.assertEqual(new_client.campaigns.count(), 2)
        # 1 empty, 1 new
        self.assertEqual(new_client.filters.count(), 2)
        self.assertEqual(new_client.choicesets.count(), 2)
        self.assertEqual(
            relational.FilterFeature.objects.filter(filter__client=new_client).count(),
            2
        )
        self.assertEqual(fb_attr.og_action, 'support')
        self.assertEqual(fb_attr.og_type, 'cause')
        self.assertEqual(
            camp.campaignproperties.get().client_faces_url,
            'https://apps.facebook.com/{}/{}/'.format(
                new_client.fb_app_name,
                encodeDES('{}/{}'.format(camp.pk, content.pk))
            )
        )
        (notification,) = mail.outbox
        self.assertIn(camp.name, notification.body)

    def test_create_campaign_wizard_topics_feature(self):
        new_client = relational.Client.objects.create(
            name='Test Client',
            fb_app_name='testing',
            fb_app_id=1,
        )
        response = self.client.post(
            reverse('targetadmin:campaign-wizard', args=[new_client.pk]), {
                # Campaign Details
                'name': 'Test Campaign',
                'error_url': 'http://www.error.com',
                'thanks_url': 'http://www.thanks.com',
                'content_url': 'http://www.content.com',
                'include_empty_fallback': 1,
                # Topics interest feature
                'enabled-filters-1': '"interest.eq.Cycling","interest.eq.Health"',
                # FB Object
                'og_title': 'Test Title',
                'org_name': 'Test Organization',
                'msg1_pre': 'Hey, ',
                'msg1_post': ' How goes it?',
                'msg2_pre': 'Hey 2, ',
                'msg2_post': ' How goes it 2?',
                'og_image': 'http://imgur.com/VsiPr',
                'sharing_prompt': 'SHARE IT',
                'sharing_button': 'Show Your Support',
                'og_description': 'Description of FB stuff',
            }
        )
        self.assertStatusCode(response, 302)
        camp = new_client.campaigns.latest('pk')
        self.assertRedirects(response,
            reverse('targetadmin:campaign-wizard-finish', args=[new_client.pk, camp.pk])
        )

        content = new_client.clientcontent.latest('pk')
        cs = camp.choice_set()

        self.assertEqual(content.url, 'http://www.content.com')
        self.assertIn('Root', cs.name)
        self.assertIn('Root', cs.choicesetfilters.get().filter.name)
        self.assertEqual(new_client.campaigns.count(), 2)
        # 1 empty, 1 new
        self.assertEqual(new_client.filters.count(), 2)
        self.assertEqual(new_client.choicesets.count(), 2)

        filters = cs.choicesetfilters.get().filter.filterfeatures.order_by('feature')
        self.assertEqual([ff.feature for ff in filters], ['topics[Cycling]', 'topics[Health]'])
        self.assertEqual({ff.feature_type.code for ff in filters}, {'topics'})
        self.assertEqual({ff.operator for ff in filters},
                         {relational.FilterFeature.Operator.MIN})
        self.assertEqual({ff.decode_value() for ff in filters},
                         {Decimal(str(settings.ADMIN_TOPICS_FILTER_THRESHOLD))})

        ranking_key = camp.campaignrankingkeys.get().ranking_key
        self.assertEqual(ranking_key.name, "Test Client Test Campaign")

        key_features = ranking_key.rankingkeyfeatures.order_by('ordinal_position')
        self.assertEqual([key.feature for key in key_features], ['topics[Cycling]', 'topics[Health]'])
        self.assertEqual({key.feature_type.code for key in key_features}, {'topics'})
        self.assertEqual({key.reverse for key in key_features}, {True})

    def test_create_campaign_wizard_no_filtering(self):
        new_client = relational.Client.objects.create(
            name='Test Client',
            fb_app_name='testing',
            fb_app_id=1,
        )
        self.assertFalse(new_client.filters.exists())
        self.assertFalse(new_client.fbobjects.exists())
        self.assertFalse(new_client.choicesets.exists())
        self.assertFalse(new_client.buttonstyles.exists())
        self.assertFalse(new_client.campaigns.exists())
        response = self.client.post(
            reverse('targetadmin:campaign-wizard', args=[new_client.pk]), {
                # Campaign Details
                'name': 'Test Campaign',
                'error_url': 'http://www.error.com',
                'thanks_url': 'http://www.thanks.com',
                'content_url': 'http://www.content.com',
                'include_empty_fallback': True,
                # FB Object
                'og_title': 'Test Title',
                'org_name': 'Test Organization',
                'msg1_pre': 'Hey, ',
                'msg1_post': ' How goes it?',
                'msg2_pre': 'Hey 2, ',
                'msg2_post': ' How goes it 2?',
                'og_image': 'http://imgur.com/VsiPr',
                'sharing_prompt': 'SHARE IT',
                'sharing_button': 'Show Your Support',
                'og_description': 'Description of FB stuff'
            }
        )
        self.assertStatusCode(response, 302)
        camp = new_client.campaigns.latest('pk')
        content = new_client.clientcontent.latest('pk')
        cs = camp.campaignchoicesets.get().choice_set
        fb_attr = camp.campaignfbobjects.get().fb_object.fbobjectattribute_set.get()
        self.assertRedirects(response,
            reverse('targetadmin:campaign-wizard-finish', args=[new_client.pk, camp.pk]),
        )
        self.assertIn('Root', cs.name)
        self.assertIn('Root', cs.choicesetfilters.get().filter.name)
        self.assertTrue(new_client.filters.exists())
        self.assertTrue(new_client.fbobjects.exists())
        self.assertTrue(new_client.choicesets.exists())
        self.assertTrue(new_client.buttonstyles.exists())
        self.assertTrue(new_client.campaigns.exists())
        self.assertEqual(new_client.campaigns.count(), 1)
        # 1 empty
        self.assertEqual(new_client.filters.count(), 1)
        self.assertEqual(new_client.choicesets.count(), 1)
        self.assertEqual(fb_attr.og_action, 'support')
        self.assertEqual(fb_attr.og_type, 'cause')
        self.assertEqual(
            camp.campaignproperties.get().client_faces_url,
            'https://apps.facebook.com/{}/{}/'.format(
                new_client.fb_app_name,
                encodeDES('{}/{}'.format(camp.pk, content.pk))
            )
        )
        (notification,) = mail.outbox
        self.assertIn(camp.name, notification.body)

    def test_campaign_wizard_no_empty_fallback(self):
        new_client = relational.Client.objects.create(
            name='Test Client',
            fb_app_name='testing',
            fb_app_id=1,
        )
        relational.Filter.objects.update(client=new_client)
        self.assertFalse(new_client.campaigns.exists())
        response = self.client.post(
            reverse('targetadmin:campaign-wizard', args=[new_client.pk]), {
                # Campaign Details
                'name': 'Test Campaign',
                'error_url': 'http://www.error.com',
                'thanks_url': 'http://www.thanks.com',
                'content_url': 'http://www.content.com',
                'include_empty_fallback': False,
                'enabled-filters-1': '"state.eq.California"',
                # FB Object
                'og_title': 'Test Title',
                'org_name': 'Test Organization',
                'msg1_pre': 'Hey, ',
                'msg1_post': ' How goes it?',
                'msg2_pre': 'Hey 2, ',
                'msg2_post': ' How goes it 2?',
                'og_image': 'http://imgur.com/VsiPr',
                'sharing_prompt': 'SHARE IT',
                'sharing_button': 'Show Your Support',
                'og_description': 'Description of FB stuff'
            }
        )
        self.assertStatusCode(response, 302)
        camp = new_client.campaigns.latest('pk')
        fb_attr = camp.campaignfbobjects.get().fb_object.fbobjectattribute_set.get()
        self.assertEqual(new_client.campaigns.count(), 1)
        self.assertEqual(fb_attr.og_action, 'support')
        self.assertEqual(fb_attr.og_type, 'cause')

    def test_campaign_wizard_existing_styles(self):
        new_client = relational.Client.objects.create(
            name='Test Client',
            fb_app_name='testing',
            fb_app_id=1,
        )
        frame_faces = relational.Page.objects.get(code='frame_faces')
        page_style = new_client.pagestyles.create(
            page=frame_faces, name='testing',
            starred=True
        )
        relational.Filter.objects.update(client=new_client)
        self.assertFalse(new_client.campaigns.exists())
        response = self.client.post(
            reverse('targetadmin:campaign-wizard', args=[new_client.pk]), {
                # Campaign Details
                'name': 'Test Campaign',
                'error_url': 'http://www.error.com',
                'thanks_url': 'http://www.thanks.com',
                'content_url': 'http://www.content.com',
                'include_empty_fallback': False,
                'enabled-filters-1': '"state.eq.California"',
                # FB Object
                'og_title': 'Test Title',
                'org_name': 'Test Organization',
                'msg1_pre': 'Hey, ',
                'msg1_post': ' How goes it?',
                'msg2_pre': 'Hey 2, ',
                'msg2_post': ' How goes it 2?',
                'og_image': 'http://imgur.com/VsiPr',
                'sharing_prompt': 'SHARE IT',
                'sharing_button': 'Show Your Support!',
                'og_description': 'Description of FB stuff'
            }
        )
        self.assertStatusCode(response, 302)
        camp = new_client.campaigns.latest('pk')
        fb_attr = camp.campaignfbobjects.get().fb_object.fbobjectattribute_set.get()
        self.assertEqual(new_client.campaigns.count(), 1)
        self.assertEqual(fb_attr.og_action, 'support')
        self.assertEqual(fb_attr.og_type, 'cause')
        # Page Style
        campaign_page_style_sets = camp.campaignpagestylesets.all()
        self.assertEqual(len(campaign_page_style_sets), 2)
        self.assertEqual(
            [campaign_page_style_set.page_style_set.page_styles.count()
             for campaign_page_style_set in campaign_page_style_sets],
            [1, 1]
        )
        page_styles_pages = (
            campaign_page_style_set.page_style_set.page_styles.values_list('page__code', flat=True)
            for campaign_page_style_set in campaign_page_style_sets
        )
        self.assertEqual(
            set(chain.from_iterable(page_styles_pages)),
            {relational.Page.BUTTON, relational.Page.FRAME_FACES}
        )
        campaign_ff_page_styles = camp.campaignpagestylesets.get(
            page_style_set__page_styles__page=frame_faces
        )
        self.assertEqual(campaign_ff_page_styles.page_style_set.page_styles.get(),
                         page_style)

    def test_campaign_wizard_finish(self):
        response = self.client.get(
            reverse('targetadmin:campaign-wizard-finish', args=[1, 1]))
        self.assertStatusCode(response, 200)

    def test_edit_campaign_wizard(self):
        new_client = relational.Client.objects.create(
            name='Test Client',
            fb_app_name='testing',
            fb_app_id=1,
        )
        self.assertFalse(new_client.campaigns.exists())
        response = self.client.post(
            reverse('targetadmin:campaign-wizard', args=[new_client.pk]), {
                # Campaign Details
                'name': 'Test Campaign',
                'error_url': 'http://www.error.com',
                'thanks_url': 'http://www.thanks.com',
                'content_url': 'http://www.content.com',
                'include_empty_fallback': False,
                'enabled-filters-1': '"state.eq.California"',
                # FB Object
                'og_title': 'Test Title',
                'org_name': 'Test Organization',
                'msg1_pre': 'Hey, ',
                'msg1_post': ' How goes it?',
                'msg2_pre': 'Hey 2, ',
                'msg2_post': ' How goes it 2?',
                'og_image': 'http://imgur.com/VsiPr',
                'sharing_prompt': 'SHARE IT',
                'sharing_button': 'Show Your Support!',
                'og_description': 'Description of FB stuff'
            }
        )
        self.assertStatusCode(response, 302)
        campaign = new_client.campaigns.get()
        content0 = new_client.clientcontent.get()
        props = campaign.campaignproperties.all()
        encoded = encodeDES('{}/{}'.format(campaign.pk, content0.pk))
        self.assertEqual(props.values_list('client_faces_url', flat=True).get(),
                         'https://apps.facebook.com/{}/{}/'.format(new_client.fb_app_name, encoded))
        self.assertIsNone(props.get().fallback_campaign)

        response = self.client.post(
            reverse('targetadmin:campaign-wizard-edit', args=[new_client.pk, campaign.pk]), {
                # Campaign Details
                'name': 'Test Campaign',
                'error_url': 'http://www.error.com',
                'thanks_url': 'http://www.thanks.com',
                'content_url': 'http://www.content.com',
                'include_empty_fallback': True,
                'enabled-filters-1': '"state.eq.California"',
                # FB Object
                'og_title': 'Test Title',
                'org_name': 'Test Organization',
                'msg1_pre': 'Hey, ',
                'msg1_post': ' How goes it?',
                'msg2_pre': 'Hey 2, ',
                'msg2_post': ' How goes it 2?',
                'og_image': 'http://imgur.com/VsiPr',
                'sharing_prompt': 'SHARE IT',
                'sharing_button': 'Show Your Support!',
                'og_description': 'Description of FB stuff'
            }
        )
        self.assertStatusCode(response, 302)
        campaign = new_client.campaigns.exclude(rootcampaign_properties=None).get()
        content = new_client.clientcontent.get()
        self.assertEqual(content, content0)
        self.assertTrue(props.get().fallback_campaign)
        encoded = encodeDES('{}/{}'.format(campaign.pk, content.pk))
        self.assertEqual(props.values_list('client_faces_url', flat=True).get(),
                         'https://apps.facebook.com/{}/{}/'.format(new_client.fb_app_name, encoded))


class TestCampaignData(TestAdminBase):

    fixtures = ['admin_test_data']

    def setUp(self):
        super(TestCampaignData, self).setUp()
        self.campaign_nofallback = (self.test_client.campaigns
                                    .exclude(rootcampaign_properties=None)
                                    .filter(campaignproperties__fallback_campaign=None))[0]
        self.campaign_wfallback = (self.test_client.campaigns
                                   .exclude(rootcampaign_properties=None)
                                   .exclude(campaignproperties__fallback_campaign=None))[0]
        self.last_fallback = relational.Campaign.objects.get(
            campaignproperties__root_campaign=self.campaign_wfallback,
            campaignproperties__fallback_campaign=None,
        )
        csf = self.campaign_wfallback.choice_set().choicesetfilters.all()
        csf0 = csf[0]
        csf.exclude(pk=csf0.pk).delete()

    def test_campaign_data_content_url(self):
        response = self.client.get(reverse('targetadmin:campaign-data',
                                           args=[self.test_client.pk, self.campaign_nofallback.pk]))
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertEqual(data['content_url'], 'http://local.edgeflip.com:8080/mocks/guncontrol')

    def test_campaign_data_no_empty_fallback0(self):
        campaign = self.campaign_nofallback
        self.assertIsNone(campaign.campaignproperties.get().fallback_campaign)
        response = self.client.get(reverse('targetadmin:campaign-data',
                                           args=[self.test_client.pk, campaign.pk]))
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertFalse(data['include_empty_fallback'])

    def test_campaign_data_no_empty_fallback1(self):
        campaign = self.campaign_wfallback
        last_fallback = self.last_fallback
        last_filter = last_fallback.choice_set().choicesetfilters.get().filter
        last_filter.filterfeatures.create(feature='gender', operator='eq', value='male')
        response = self.client.get(reverse('targetadmin:campaign-data',
                                           args=[self.test_client.pk, campaign.pk]))
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertFalse(data['include_empty_fallback'])

    def test_campaign_data_empty_fallback(self):
        campaign = self.campaign_wfallback
        last_fallback = self.last_fallback
        last_fallback.choice_set().choicesetfilters.get().filter.filterfeatures.all().delete()
        response = self.client.get(reverse('targetadmin:campaign-data',
                                           args=[self.test_client.pk, campaign.pk]))
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertTrue(data['include_empty_fallback'])


class TestCampaignSummary(TestAdminBase):

    fixtures = ['admin_test_data']

    def test_campaign_data(self):
        response = self.client.get(reverse('targetadmin:campaign-summary',
                                           args=[self.test_client.pk, 1]))
        self.assertStatusCode(response, 200)

        context = response.context
        self.assertEqual(context['campaign_id'], 1)
        self.assertEqual(context['create_dt'], '2013-07-15T16:38:28+00:00')
        self.assertEqual(json.loads(context['campaign_properties']), {
            'status': 'draft',
            'client_faces_url': 'http://local.edgeflip.com:8080/mocks/guncontrol_share',
            'client_thanks_url': 'https://donate.demandaction.org/act/donate',
            'client_error_url': 'https://donate.demandaction.org/act/donate',
        })


class TestPublishCampaign(TestAdminBase):

    fixtures = ['admin_test_data']

    def setUp(self):
        super(TestPublishCampaign, self).setUp()
        self.campaign = relational.Campaign.objects.get(pk=1)
        self.url = reverse('targetadmin:publish-campaign',
                           args=[self.test_client.pk, self.campaign.pk])

        self.assertEqual(self.campaign.status(), Status.DRAFT)

    def test_publish_campaign(self):
        response = self.client.post(self.url)
        summary_url = reverse('targetadmin:campaign-summary',
                              args=[self.test_client.pk, self.campaign.pk])
        self.assertRedirects(response, summary_url)
        self.assertEqual(self.campaign.status(), Status.PUBLISHED)

    def test_publish_get_disallowed(self):
        response = self.client.get(self.url)
        self.assertStatusCode(response, 405)
        self.assertEqual(self.campaign.status(), Status.DRAFT)

    def test_publish_fallback_disallowed(self):
        fallback = self.test_client.campaigns.get(pk=4)
        url = reverse('targetadmin:publish-campaign',
                      args=[self.test_client.pk, fallback.pk])
        response = self.client.post(url)
        self.assertStatusCode(response, 404)
        self.assertEqual(fallback.status(), Status.DRAFT)

    def test_publish_published_disallowed(self):
        self.campaign.campaignproperties.update(
            status=Status.INACTIVE
        )
        response = self.client.post(self.url)
        self.assertStatusCode(response, 400)
        self.assertEqual(self.campaign.status(), Status.INACTIVE)


class TestArchiveCampaign(TestAdminBase):

    fixtures = ['admin_test_data']

    def setUp(self):
        super(TestArchiveCampaign, self).setUp()
        self.campaign = relational.Campaign.objects.get(pk=1)
        self.url = reverse('targetadmin:archive-campaign',
                           args=[self.test_client.pk, self.campaign.pk])

        self.campaign.rootcampaign_properties.update(status=Status.PUBLISHED)

    def test_archive_campaign(self):
        response = self.client.post(self.url)
        summary_url = reverse('targetadmin:campaign-summary',
                              args=[self.test_client.pk, self.campaign.pk])
        self.assertRedirects(response, summary_url)
        self.assertEqual(self.campaign.status(), Status.INACTIVE)

    def test_archive_get_disallowed(self):
        response = self.client.get(self.url)
        self.assertStatusCode(response, 405)
        self.assertEqual(self.campaign.status(), Status.PUBLISHED)

    def test_archive_fallback_disallowed(self):
        fallback = self.test_client.campaigns.get(pk=4)
        fallback.campaignproperties.update(status=Status.PUBLISHED)
        url = reverse('targetadmin:archive-campaign',
                      args=[self.test_client.pk, fallback.pk])
        response = self.client.post(url)
        self.assertStatusCode(response, 404)
        self.assertEqual(fallback.status(), Status.PUBLISHED)

    def test_superuser_required(self):
        User.objects.filter(username='tester').update(is_superuser=False)
        response = self.client.post(self.url)
        self.assertStatusCode(response, 403)
        self.assertEqual(self.campaign.status(), Status.PUBLISHED)
