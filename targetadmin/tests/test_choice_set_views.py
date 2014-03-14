from django.core.urlresolvers import reverse

from . import TestAdminBase
from targetshare.models import relational


class TestChoiceSetViews(TestAdminBase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestChoiceSetViews, self).setUp()
        self.cs = self.test_client.choicesets.create(name='test_cs_object')

    def test_cs_list_view(self):
        ''' View a listing of Choice Set objects '''
        response = self.client.get(
            reverse('targetadmin:cs-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_cs_detail_view(self):
        ''' Test viewing a specific Choice Set object '''
        response = self.client.get(
            reverse('targetadmin:cs-detail', args=[self.test_client.pk, self.cs.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object']

    def test_create_cs_object(self):
        ''' Test creating a new Choice Set object '''
        response = self.client.post(
            reverse('targetadmin:cs-new', args=[self.test_client.pk]),
            {'name': 'test_create_cs_object', 'client': self.test_client.pk}
        )
        cs = relational.ChoiceSet.objects.get(
            name='test_create_cs_object'
        )
        self.assertStatusCode(response, 302)
        self.assertRedirects(
            response,
            reverse('targetadmin:cs-detail', args=[self.test_client.pk, cs.pk])
        )

    def test_cs_edit(self):
        """ Test that edits an existing Choice Set object and
        Choice Set Filter while also adding a new Choice Set Filter
        """
        filter_obj = self.test_client.filters.create(name='edit_view')
        csf = self.cs.choicesetfilters.create(
            choice_set=self.cs, filter=filter_obj, url_slug='edit_view')
        response = self.client.post(
            reverse('targetadmin:cs-edit', args=[self.test_client.pk, self.cs.pk]),
            {
                'name': 'edit_view_test',
                'description': 'edit view desc',
                'client': self.test_client.pk,
                'form-0-choice_set': self.cs.pk,
                'form-0-filter': filter_obj.pk,
                'form-0-choice_set_filter_id': csf.pk,
                'form-0-propensity_model_type': '',
                'form-0-end_dt': '2020-01-01',
                'form-0-url_slug': 'test-slug',
                'form-1-choice_set': self.cs.pk,
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
            reverse('targetadmin:cs-detail', args=[self.test_client.pk, self.cs.pk])
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
