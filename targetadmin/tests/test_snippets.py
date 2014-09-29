import json
import urlparse

from django.core.urlresolvers import resolve, reverse

from chapo.models import ShortenedUrl
from targetshare import utils
from targetshare.models import relational

from . import TestAdminBase


class TestSnippetViews(TestAdminBase):

    fixtures = ['admin_test_data']

    def setUp(self):
        super(TestSnippetViews, self).setUp()
        self.content = self.test_client.clientcontent.create(name='Test Content')
        self.campaign = self.test_client.campaigns.create(name='Test Campaign')
        self.campaign.campaignproperties.create()
        self.url = reverse('targetadmin:snippets', args=[self.test_client.pk])

    def test_snippets(self):
        ''' Test the views.snippets.snippets view '''
        response = self.client.get(self.url)
        self.assertStatusCode(response, 200)
        assert response.context['client']
        assert response.context['campaign']
        assert response.context['content']
        assert response.context['slug']
        assert response.context['fb_oauth_url']

        short_url = response.context['initial_url']
        short_match = resolve(short_url)
        short = ShortenedUrl.objects.get(pk=short_match.kwargs['slug'])
        self.assertEqual(short.url, response.context['fb_oauth_url'])

        form = response.context['snippet_form']
        form_campaigns = form.fields['campaign'].queryset
        self.assertTrue(form_campaigns.filter(pk=self.campaign.pk).exists())

    def test_specified_snippets(self):
        ''' Test that campaign_pk and content_pk GET args are respected '''
        campaign = relational.Campaign.objects.get(pk=2)
        content = relational.ClientContent.objects.get(pk=2)
        response = self.client.get(self.url, {
            'campaign_pk': campaign.pk,
            'content_pk': content.pk,
        })
        self.assertEqual(response.context['campaign'], campaign)
        self.assertEqual(response.context['content'], content)

    def test_snippet_update(self):
        ''' Test the encoding campaign endpoint '''
        shorts = ShortenedUrl.objects.values_list('url', flat=True)
        self.assertEqual(shorts.count(), 0)

        response = self.client.get(
            reverse('targetadmin:snippet-update', args=[self.test_client.pk]),
            {'campaign': self.campaign.pk, 'content': self.content.pk},
        )
        self.assertStatusCode(response, 200)

        data = json.loads(response.content)
        self.assertEqual(
            data['slug'],
            utils.encodeDES('%s/%s' % (self.campaign.pk, self.content.pk))
        )
        oauth_url = data['fb_oauth_url']
        parsed = urlparse.urlparse(oauth_url)
        query = urlparse.parse_qs(parsed.query)
        redirect_uri = query['redirect_uri'][0]
        self.assertEqual(
            redirect_uri,
            utils.incoming_redirect(False, 'testserver',
                                    self.campaign.pk, self.content.pk)
        )
        self.assertEqual(shorts.get(), oauth_url)

    def test_snippets_empty(self):
        self.campaign.delete()
        response = self.client.get(self.url)
        self.assertStatusCode(response, 200)
