from django.core.urlresolvers import reverse

from . import TestAdminBase
from targetshare.models import relational


class TestButtonViews(TestAdminBase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestButtonViews, self).setUp()
        self.button = self.test_client.buttonstyles.create(
            name='test object')

    def test_button_list_view(self):
        ''' Test viewing a list of Button Styles '''
        response = self.client.get(
            reverse('targetadmin:button-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_button_detail(self):
        ''' Test viewing a specific Button Style object '''
        response = self.client.get(
            reverse('targetadmin:button-detail', args=[self.test_client.pk, self.button.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object']

    def test_create_button_object(self):
        ''' Test creation of a Button Style object '''
        response = self.client.post(
            reverse('targetadmin:button-new', args=[self.test_client.pk]),
            {
                'name': 'Test Object',
                'html_template': 'test.html',
                'css_file': 'test.css'
            }
        )
        bsf = relational.ButtonStyleFile.objects.get(html_template='test.html')
        self.assertRedirects(
            response,
            reverse('targetadmin:button-detail', args=[self.test_client.pk, bsf.button_style.pk])
        )
        self.assertEqual(bsf.button_style.name, 'Test Object')
        self.assertEqual(bsf.html_template, 'test.html')
        self.assertEqual(bsf.css_file, 'test.css')

    def test_edit_button_object(self):
        ''' Test editing a Button Style Object '''
        bsf = self.button.buttonstylefiles.create()
        response = self.client.post(
            reverse('targetadmin:button-edit', args=[self.test_client.pk, self.button.pk]),
            {
                'name': 'Edit Test Edited',
                'html_template': 'test.html',
                'css_file': 'test.css',
                'button_style': self.button.pk
            }
        )
        button = relational.ButtonStyle.objects.get(pk=self.button.pk)
        bsf = button.buttonstylefiles.get()
        self.assertRedirects(
            response,
            reverse('targetadmin:button-detail', args=[self.test_client.pk, self.button.pk])
        )
        self.assertEqual(bsf.button_style.name, 'Edit Test Edited')
        self.assertEqual(bsf.html_template, 'test.html')
        self.assertEqual(bsf.css_file, 'test.css')
