from django.core.urlresolvers import reverse

from . import TestAdminBase
from targetshare.models import relational


class TestFilterViews(TestAdminBase):

    fixtures = ['targetadmin_test_data']

    def setUp(self):
        super(TestFilterViews, self).setUp()
        self.filter_obj = self.test_client.filters.create(name='test filter')

    def test_filter_list_view(self):
        ''' View a listing of filter objects '''
        response = self.client.get(
            reverse('filter-list', args=[self.test_client.pk])
        )
        self.assertStatusCode(response, 200)
        assert response.context['object_list']

    def test_filter_detail_view(self):
        ''' Test viewing a specific filter object '''
        response = self.client.get(
            reverse('filter-detail', args=[self.test_client.pk, self.filter_obj.pk])
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
        ff = self.filter_obj.filterfeatures.create(
            feature='age',
            operator='eq',
            value=15,
            value_type='int'
        )
        response = self.client.post(
            reverse('filter-edit', args=[self.test_client.pk, self.filter_obj.pk]),
            {
                'name': 'edit_view_test',
                'description': 'edit view desc',
                'client': self.test_client.pk,
                'form-0-filter': self.filter_obj.pk,
                'form-0-filter_feature_id': ff.pk,
                'form-0-feature': relational.FilterFeature.AGE,
                'form-0-value': 25,
                'form-0-operator': 'eq',
                'form-0-end_dt': '2010-1-1',
                'form-1-filter': self.filter_obj.pk,
                'form-1-filter_feature_id': '',
                'form-1-feature': relational.FilterFeature.STATE,
                'form-1-value': 'Illinois',
                'form-1-operator': 'in',
                'form-1-end_dt': '2010-1-1',
                'form-INITIAL_FORMS': 1,
                'form-TOTAL_FORMS': 2,
                'form-MAX_NUM_FORMS': 1000,
            }
        )
        self.assertRedirects(
            response,
            reverse('filter-detail', args=[self.test_client.pk, self.filter_obj.pk])
        )
        filter_obj = self.test_client.filters.get(name='edit_view_test')
        ff = filter_obj.filterfeatures.get(pk=ff.pk)

        # Filter Changes
        self.assertEqual(filter_obj.description, 'edit view desc')
        self.assertEqual(filter_obj.filterfeatures.count(), 2)
        # Feature Changes
        self.assertEqual(ff.value, '25')
        self.assertEqual(ff.value_type, 'int')
        # New Feature
        new_ff = filter_obj.filterfeatures.get(value='Illinois')
        self.assertEqual(new_ff.operator, 'in')
        self.assertEqual(new_ff.value_type, 'string')
