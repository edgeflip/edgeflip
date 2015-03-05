import re

from django.core.urlresolvers import reverse

from targetshare import models

from .. import EdgeFlipViewTestCase


class TestButtonViews(EdgeFlipViewTestCase):

    fixtures = ['test_data']

    def test_button_no_recs(self):
        ''' Tests views.button without style recs '''
        assert not models.Assignment.objects.exists()

        response = self.client.get(reverse('targetshare:button-default', args=[1, 1]))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['fb_params'],
            {'fb_app_name': 'sharing-social-good',
             'fb_app_id': 471727162864364}
        )

        assignment = models.Assignment.objects.get()
        self.assertEqual(assignment.feature_type, 'page_style_set_id')

    def test_button_with_recs(self):
        ''' Tests views.button with style recs '''
        # Create Button Styles
        campaign = models.Campaign.objects.get(pk=1)
        button = models.Page.objects.get_button()

        models.PageStyleSet.objects.filter(
            page_styles__page=button,
            campaignpagestyleset__campaign=campaign,
        ).delete() # clear existing
        for prob in xrange(1, 3):
            page_style = campaign.client.pagestyles.create(
                name="My styles {}".format(prob),
                page=button,
                url='http://AWESOMEDOMAIN/AWESOME-{}.CSS'.format(prob),
            )
            page_style_set = page_style.pagestylesets.create()
            campaign.campaignpagestylesets.create(
                page_style_set=page_style_set,
                rand_cdf=prob / 2.0 # [0.5, 1]
            )

        self.assertFalse(models.Assignment.objects.exists())
        response = self.client.get(reverse('targetshare:button-default', args=[1, 1]))

        self.assertContains(response, '//AWESOMEDOMAIN/AWESOME-', count=1)

        assignment = models.Assignment.objects.get()
        chosen_from_rows = re.findall(r'\d+', assignment.chosen_from_rows)
        options = campaign.campaignpagestylesets.filter(
            page_style_set__page_styles__page=button,
        ).values_list('pk', flat=True)
        self.assertItemsEqual(map(int, chosen_from_rows), options)
        self.assertIn(assignment.feature_row, options)
        self.assertEqual(assignment.feature_type, 'page_style_set_id')

        page_style = models.PageStyle.objects.get(pagestylesets=assignment.feature_row)
        link_html = '<link rel="stylesheet" type="text/css" href="{}" />'.format(page_style.href)
        self.assertContains(response, link_html, count=1, html=True)

        self.assertEqual(models.Event.objects.filter(event_type='session_start').count(), 1)
