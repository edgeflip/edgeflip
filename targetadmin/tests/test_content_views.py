from django.core.urlresolvers import reverse

from . import TestAdminBase
from targetshare.models import relational


class TestContentViews(TestAdminBase):

    fixtures = ['test_data']

    def test_content_list_view(self):
        ''' Test viewing a content list '''
        response = self.client.get(
            reverse('targetadmin:content-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_content_detail_view(self):
        ''' Test viewing a content object '''
        response = self.client.get(
            reverse('targetadmin:content-detail', args=[self.test_client.pk, self.test_content.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object']

    def test_content_detail_invalid_client(self):
        ''' Test viewing a content object with a non-matching client '''
        new_client = relational.Client.objects.create(name='No good')
        response = self.client.get(
            reverse('targetadmin:content-detail', args=[new_client.pk, self.test_content.pk])
        )
        self.assertStatusCode(response, 404)

    def test_create_new_content_object(self):
        ''' Create a new content object '''
        response = self.client.post(
            reverse('targetadmin:content-new', args=[self.test_client.pk]),
            {'name': 'New Content', 'client': self.test_client.pk}
        )
        self.assertStatusCode(response, 302)
        obj = relational.ClientContent.objects.get(
            client=self.test_client,
            name='New Content'
        )
        self.assertRedirects(
            response,
            reverse('targetadmin:content-detail', args=[self.test_client.pk, obj.pk])
        )

    def test_edit_content_object(self):
        content = relational.ClientContent.objects.create(name='Edit Test')
        response = self.client.post(
            reverse('targetadmin:content-edit', args=[self.test_client.pk, content.pk]),
            {'name': 'Edit Content Test', 'client': self.test_client.pk}
        )
        content = relational.ClientContent.objects.get(pk=content.pk)
        self.assertEqual(content.name, 'Edit Content Test')
        self.assertRedirects(
            response,
            reverse('targetadmin:content-detail', args=[self.test_client.pk, content.pk])
        )
