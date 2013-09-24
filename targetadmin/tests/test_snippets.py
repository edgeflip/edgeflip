from django.core.urlresolvers import reverse

from . import TestAdminBase
from targetshare.utils import encodeDES


class TestSnippetViews(TestAdminBase):

    fixtures = ['targetadmin_test_data']

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

    def test_encode_campaign(self):
        ''' Test the encoding campaign endpoint '''
        response = self.client.get(
            reverse('encode', args=[self.test_client.pk, self.campaign.pk, self.content.pk])
        )
        self.assertStatusCode(response, 200)
        self.assertEqual(
            response.content,
            encodeDES('%s/%s' % (self.campaign.pk, self.content.pk))
        )