import re
from decimal import Decimal

from django.core.urlresolvers import reverse
from mock import patch

from targetshare import models

from .. import EdgeFlipViewTestCase


@patch.dict('django.conf.settings.WEB', mock_subdomain='testserver')
class TestButtonViews(EdgeFlipViewTestCase):

    fixtures = ['test_data']

    def test_button_no_recs(self):
        ''' Tests views.button without style recs '''
        assert not models.Assignment.objects.exists()

        response = self.client.get(reverse('button', args=[1, 1]))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['fb_params'],
            {'fb_app_name': 'sharing-social-good',
             'fb_app_id': 471727162864364}
        )

        assignment = models.Assignment.objects.get()
        # This field is how we know the assignment came from a default:
        self.assertIsNone(assignment.feature_row)

    def test_button_with_recs(self):
        ''' Tests views.button with style recs '''
        # Create Button Styles
        campaign = models.Campaign.objects.get(pk=1)
        client = campaign.client
        for prob in xrange(1, 3):
            bs = client.buttonstyles.create(name='test')
            bs.buttonstylefiles.create(html_template='button.html')
            true_prob = prob / 2.0 # [0.5, 1]
            campaign.campaignbuttonstyles.create(
                button_style=bs, rand_cdf=Decimal(true_prob))

        assert not models.Assignment.objects.exists()
        response = self.client.get(reverse('button', args=[1, 1]))

        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['fb_params'],
            {'fb_app_name': 'sharing-social-good',
             'fb_app_id': 471727162864364}
        )
        assignment = models.Assignment.objects.get()
        chosen_from_rows = re.findall(r'\d+', assignment.chosen_from_rows)
        self.assertEqual(
            {int(choice) for choice in chosen_from_rows},
            set(campaign.campaignbuttonstyles.values_list('pk', flat=True))
        )
        self.assertEqual(models.Event.objects.filter(event_type='session_start').count(), 1)
