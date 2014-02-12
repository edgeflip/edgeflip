import json

from django.core.urlresolvers import reverse

from . import TestAdminBase
from targetshare.utils import encodeDES
from targetshare.models import relational


class TestSnippetViews(TestAdminBase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestSnippetViews, self).setUp()
        self.campaign = self.test_client.campaigns.create(
            name='Test Campaign')
        self.content = self.test_client.clientcontent.create(
            name='Test Content')

    def test_snippets(self):
        ''' Test the views.snippets.snippets view '''
        response = self.client.get(reverse('snippets', args=[self.test_client.pk]))
        self.assertStatusCode(response, 200)
        assert response.context['client']
        assert response.context['first_campaign']
        assert response.context['first_content']

    def test_specified_snippets(self):
        ''' Test that campaign_pk and content_pk GET args are respected '''
        campaign = relational.Campaign.objects.get(pk=2)
        content = relational.ClientContent.objects.get(pk=2)
        response = self.client.get('{}?campaign_pk={}&content_pk={}'.format(
            reverse('snippets', args=[self.test_client.pk]),
            campaign.pk,
            content.pk,
        ))
        self.assertEqual(response.context['first_campaign'], campaign)
        self.assertEqual(response.context['first_content'], content)

    def test_snippet_update(self):
        ''' Test the encoding campaign endpoint '''
        response = self.client.get(
            reverse('snippet-update', args=[
                self.test_client.pk, self.campaign.pk, self.content.pk
            ])
        )
        self.assertStatusCode(response, 200)
        json_data = json.loads(response.content)
        self.assertEqual(
            json_data['slug'],
            encodeDES('%s/%s' % (self.campaign.pk, self.content.pk))
        )
        self.assertEqual(
            json_data['faces_url'],
            "http%3A%2F%2Ftestserver%2Fincoming%2FlSJLSpMCF7U%253D%2F"
        )
