from django.core.urlresolvers import reverse

from . import TestAdminBase
from targetshare.models import relational


class TestFBObjectViews(TestAdminBase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestFBObjectViews, self).setUp()
        self.fb_obj = self.test_client.fbobjects.create(name='test object')

    def test_fb_obj_list_view(self):
        ''' Test viewing a list of fb_objs '''
        response = self.client.get(
            reverse('targetadmin:fb-obj-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_fb_obj_detail(self):
        ''' Test viewing a specific FB object '''
        response = self.client.get(
            reverse('targetadmin:fb-obj-detail', args=[self.test_client.pk, self.fb_obj.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object']

    def test_create_fb_object(self):
        ''' Test creation of a FB object '''
        response = self.client.post(
            reverse('targetadmin:fb-obj-new', args=[self.test_client.pk]),
            {
                'name': 'Test Object',
                'og_title': 'Test Title',
                'sharing_prompt': 'Test Prompt',
            }
        )
        fb_obj_attr = relational.FBObjectAttribute.objects.get(
            og_title='Test Title')
        self.assertRedirects(
            response,
            reverse('targetadmin:fb-obj-detail', args=[self.test_client.pk, fb_obj_attr.fb_object.pk])
        )
        self.assertEqual(fb_obj_attr.fb_object.name, 'Test Object')
        self.assertEqual(fb_obj_attr.og_title, 'Test Title')

    def test_edit_fb_object(self):
        ''' Test editing a FB Object '''
        fb_obj_attr = self.fb_obj.fbobjectattribute_set.create(
            og_title='Attr Edit Test')
        response = self.client.post(
            reverse('targetadmin:fb-obj-edit', args=[self.test_client.pk, self.fb_obj.pk]),
            {
                'name': 'Edit Test Edited',
                'og_title': 'Test Title Edited',
                'sharing_prompt': 'Test Prompt',
            }
        )
        fb_obj = relational.FBObject.objects.get(pk=self.fb_obj.pk)
        fb_obj_attr = fb_obj.fbobjectattribute_set.get()
        self.assertRedirects(
            response,
            reverse('targetadmin:fb-obj-detail', args=[self.test_client.pk, fb_obj.pk])
        )
        self.assertEqual(fb_obj_attr.fb_object.name, 'Edit Test Edited')
        self.assertEqual(fb_obj_attr.og_title, 'Test Title Edited')
