from django.core.urlresolvers import reverse

from targetshare.tests import EdgeFlipTestCase
from targetshare.models import relational


class TargetAdminTest(EdgeFlipTestCase):

    fixtures = ['targetadmin_test_data']

    def setUp(self):
        super(TargetAdminTest, self).setUp()
        self.test_client = relational.Client.objects.create(
            name='Testing Client',
            _fb_app_id=1234,
            _fb_app_name='That One App',
            domain='example.com',
            subdomain='test',
        )
        self.test_content = relational.ClientContent.objects.create(
            name='Testing Content',
            client=self.test_client
        )
        assert self.client.login(
            username='tester',
            password='testing',
        )

    def test_client_list(self):
        """ Test client listing """
        response = self.client.get(reverse('client-list'))
        self.assertStatusCode(response, 200)
        assert response.context['client_list']

    def test_client_detail(self):
        """ Test client detail view """
        response = self.client.get(reverse(
            'client-detail', args=[self.test_client.pk]))
        self.assertStatusCode(response, 200)
        self.assertEqual(response.context['client'].name, 'Testing Client')

    def test_create_new_client_get(self):
        """ Test new client view via GET"""
        response = self.client.get(reverse('client-new'))
        self.assertStatusCode(response, 200)
        assert response.context['form']

    def test_create_new_client_post(self):
        """ Test creating a new client object """
        response = self.client.post(reverse('client-new'), {
            'name': 'Test',
        })
        self.assertStatusCode(response, 302)

    def test_content_list_view(self):
        ''' Test viewing a content list '''
        response = self.client.get(
            reverse('content-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_content_detail_view(self):
        ''' Test viewing a content object '''
        response = self.client.get(
            reverse('content-detail', args=[self.test_client.pk, self.test_content.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object']

    def test_content_detail_invalid_client(self):
        ''' Test viewing a content object with a non-matching client '''
        new_client = relational.Client.objects.create(name='No good')
        response = self.client.get(
            reverse('content-detail', args=[new_client.pk, self.test_content.pk])
        )
        self.assertStatusCode(response, 404)

    def test_create_new_content_object(self):
        ''' Create a new content object '''
        response = self.client.post(
            reverse('content-new', args=[self.test_client.pk]),
            {'name': 'New Content', 'client': self.test_client.pk}
        )
        self.assertStatusCode(response, 302)
        obj = relational.ClientContent.objects.get(
            client=self.test_client,
            name='New Content'
        )
        self.assertRedirects(
            response,
            reverse('content-detail', args=[self.test_client.pk, obj.pk])
        )

    def test_edit_content_object(self):
        content = relational.ClientContent.objects.create(name='Edit Test')
        response = self.client.post(
            reverse('content-edit', args=[self.test_client.pk, content.pk]),
            {'name': 'Edit Content Test', 'client': self.test_client.pk}
        )
        content = relational.ClientContent.objects.get(pk=content.pk)
        self.assertEqual(content.name, 'Edit Content Test')
        self.assertRedirects(
            response,
            reverse('content-detail', args=[self.test_client.pk, content.pk])
        )

    def test_fb_obj_list_view(self):
        ''' Test viewing a list of fb_objs '''
        self.test_client.fbobject_set.create(name='test object')
        response = self.client.get(
            reverse('fb-obj-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_fb_obj_detail(self):
        ''' Test viewing a specific FB object '''
        fb_obj = self.test_client.fbobject_set.create(name='test object')
        response = self.client.get(
            reverse('fb-obj-detail', args=[self.test_client.pk, fb_obj.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object']

    def test_create_fb_object(self):
        ''' Test creation of a FB object '''
        response = self.client.post(
            reverse('fb-obj-new', args=[self.test_client.pk]),
            {
                'name': 'Test Object',
                'og_title': 'Test Title'
            }
        )
        fb_obj_attr = relational.FBObjectAttribute.objects.get(
            og_title='Test Title')
        self.assertRedirects(
            response,
            reverse('fb-obj-detail', args=[self.test_client.pk, fb_obj_attr.fb_object.pk])
        )
        self.assertEqual(fb_obj_attr.fb_object.name, 'Test Object')
        self.assertEqual(fb_obj_attr.og_title, 'Test Title')

    def test_edit_fb_object(self):
        ''' Test editing a FB Object '''
        fb_obj = self.test_client.fbobject_set.create(name='test object')
        fb_obj_attr = fb_obj.fbobjectattribute_set.create(og_title='Attr Edit Test')
        response = self.client.post(
            reverse('fb-obj-edit', args=[self.test_client.pk, fb_obj.pk]),
            {
                'name': 'Edit Test Edited',
                'og_title': 'Test Title Edited'
            }
        )
        fb_obj = relational.FBObject.objects.get(pk=fb_obj.pk)
        fb_obj_attr = fb_obj.fbobjectattribute_set.get()
        self.assertRedirects(
            response,
            reverse('fb-obj-detail', args=[self.test_client.pk, fb_obj.pk])
        )
        self.assertEqual(fb_obj_attr.fb_object.name, 'Edit Test Edited')
        self.assertEqual(fb_obj_attr.og_title, 'Test Title Edited')

    def test_filter_list_view(self):
        ''' View a listing of filter objects '''
        self.test_client.filters.create(name='list_view_test')
        response = self.client.get(
            reverse('filter-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_filter_detail_view(self):
        ''' Test viewing a specific filter object '''
        filter_obj = self.test_client.filters.create(name='detail_view')
        response = self.client.get(
            reverse('filter-detail', args=[self.test_client.pk, filter_obj.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object']

    def test_create_filter_object(self):
        ''' Test creating a new filter object '''
        response = self.client.post(
            reverse('filter-new', args=[self.test_client.pk]),
            {'name': 'test_create_filter_object', 'client': self.test_client.pk}
        )
        filter_obj = relational.Filter.objects.get(
            name='test_create_filter_object'
        )
        self.assertStatusCode(response, 302)
        self.assertRedirects(
            response,
            reverse('filter-detail', args=[self.test_client.pk, filter_obj.pk])
        )

    def test_filter_edit(self):
        """ Test that edits an existing filter object and filter feature while
        also adding a new filter feature
        """
        filter_obj = self.test_client.filters.create(name='edit_view')
        ff = filter_obj.filterfeatures.create(
            feature='age',
            operator='eq',
            value=15,
            value_type='int'
        )
        response = self.client.post(
            reverse('filter-edit', args=[self.test_client.pk, filter_obj.pk]),
            {
                'name': 'edit_view_test',
                'description': 'edit view desc',
                'client': self.test_client.pk,
                'form-0-filter': filter_obj.pk,
                'form-0-filter_feature_id': ff.pk,
                'form-0-feature': relational.FilterFeature.AGE,
                'form-0-value': 25,
                'form-0-value_type': 'int',
                'form-0-operator': 'eq',
                'form-0-end_dt': '2010-1-1',
                'form-1-filter': filter_obj.pk,
                'form-1-filter_feature_id': '',
                'form-1-feature': relational.FilterFeature.STATE,
                'form-1-value': 'Illinois',
                'form-1-operator': 'in',
                'form-1-value_type': 'string',
                'form-1-end_dt': '2010-1-1',
                'form-INITIAL_FORMS': 1,
                'form-TOTAL_FORMS': 2,
                'form-MAX_NUM_FORMS': 1000,
            }
        )
        self.assertRedirects(
            response,
            reverse('filter-detail', args=[self.test_client.pk, filter_obj.pk])
        )
        filter_obj = self.test_client.filters.get(name='edit_view_test')
        ff = filter_obj.filterfeatures.get(pk=ff.pk)

        # Filter Changes
        self.assertEqual(filter_obj.description, 'edit view desc')
        self.assertEqual(filter_obj.filterfeatures.count(), 2)
        # Feature Changes
        self.assertEqual(ff.value, '25')
        # New Feature
        new_ff = filter_obj.filterfeatures.get(value='Illinois')
        self.assertEqual(new_ff.operator, 'in')

    def test_cs_list_view(self):
        ''' View a listing of Choice Set objects '''
        self.test_client.choicesets.create(name='list_view_test')
        response = self.client.get(
            reverse('cs-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_cs_detail_view(self):
        ''' Test viewing a specific Choice Set object '''
        cs = self.test_client.choicesets.create(name='detail_view')
        response = self.client.get(
            reverse('cs-detail', args=[self.test_client.pk, cs.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object']

    def test_create_cs_object(self):
        ''' Test creating a new Choice Set object '''
        response = self.client.post(
            reverse('cs-new', args=[self.test_client.pk]),
            {'name': 'test_create_cs_object', 'client': self.test_client.pk}
        )
        cs = relational.ChoiceSet.objects.get(
            name='test_create_cs_object'
        )
        self.assertStatusCode(response, 302)
        self.assertRedirects(
            response,
            reverse('cs-detail', args=[self.test_client.pk, cs.pk])
        )

    def test_cs_edit(self):
        """ Test that edits an existing Choice Set object and
        Choice Set Filter while also adding a new Choice Set Filter
        """
        filter_obj = self.test_client.filters.create(name='edit_view')
        cs = self.test_client.choicesets.create(name='edit_view')
        csf = cs.choicesetfilters.create(
            choice_set=cs, filter=filter_obj, url_slug='edit_view')
        response = self.client.post(
            reverse('cs-edit', args=[self.test_client.pk, cs.pk]),
            {
                'name': 'edit_view_test',
                'description': 'edit view desc',
                'client': self.test_client.pk,
                'form-0-choice_set': cs.pk,
                'form-0-filter': filter_obj.pk,
                'form-0-choice_set_filter_id': csf.pk,
                'form-0-propensity_model_type': '',
                'form-0-end_dt': '2020-01-01',
                'form-0-url_slug': 'test-slug',
                'form-1-choice_set': cs.pk,
                'form-1-filter': filter_obj.pk,
                'form-1-choice_set_filter_id': '',
                'form-1-propensity_model_type': '',
                'form-1-end_dt': '2020-01-01',
                'form-1-url_slug': 'new-slug',
                'form-INITIAL_FORMS': 1,
                'form-TOTAL_FORMS': 2,
                'form-MAX_NUM_FORMS': 1000,
            }
        )
        self.assertRedirects(
            response,
            reverse('cs-detail', args=[self.test_client.pk, cs.pk])
        )
        cs = self.test_client.choicesets.get(name='edit_view_test')
        csf = relational.ChoiceSetFilter.objects.get(pk=csf.pk)

        # CS Changes
        self.assertEqual(cs.description, 'edit view desc')
        self.assertEqual(cs.choicesetfilters.count(), 2)
        # CSF Changes
        self.assertEqual(csf.url_slug, 'test-slug')
        # New CSF
        new_csf = cs.choicesetfilters.get(url_slug='new-slug')
        self.assertEqual(new_csf.url_slug, 'new-slug')

    def test_button_list_view(self):
        ''' Test viewing a list of Button Styles '''
        self.test_client.buttonstyle_set.create(name='test object')
        response = self.client.get(
            reverse('button-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_button_detail(self):
        ''' Test viewing a specific Button Style object '''
        button = self.test_client.buttonstyle_set.create(name='test object')
        response = self.client.get(
            reverse('button-detail', args=[self.test_client.pk, button.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object']

    def test_create_button_object(self):
        ''' Test creation of a Button Style object '''
        response = self.client.post(
            reverse('button-new', args=[self.test_client.pk]),
            {
                'name': 'Test Object',
                'html_template': 'test.html',
                'css_file': 'test.css'
            }
        )
        bsf = relational.ButtonStyleFile.objects.get(html_template='test.html')
        self.assertRedirects(
            response,
            reverse('button-detail', args=[self.test_client.pk, bsf.button_style.pk])
        )
        self.assertEqual(bsf.button_style.name, 'Test Object')
        self.assertEqual(bsf.html_template, 'test.html')
        self.assertEqual(bsf.css_file, 'test.css')

    def test_edit_button_object(self):
        ''' Test editing a Button Style Object '''
        button = self.test_client.buttonstyle_set.create(name='test object')
        bsf = button.buttonstylefiles.create()
        response = self.client.post(
            reverse('button-edit', args=[self.test_client.pk, button.pk]),
            {
                'name': 'Edit Test Edited',
                'html_template': 'test.html',
                'css_file': 'test.css',
                'button_style': button.pk
            }
        )
        button = relational.ButtonStyle.objects.get(pk=button.pk)
        bsf = button.buttonstylefiles.get()
        self.assertRedirects(
            response,
            reverse('button-detail', args=[self.test_client.pk, button.pk])
        )
        self.assertEqual(bsf.button_style.name, 'Edit Test Edited')
        self.assertEqual(bsf.html_template, 'test.html')
        self.assertEqual(bsf.css_file, 'test.css')
