import json

from django.core.urlresolvers import reverse

from . import TestAdminBase
from targetshare.models import relational


class TestFilterViews(TestAdminBase):

    fixtures = ['test_data']

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
                # Filter Feature 1
                'form-0-filter': self.filter_obj.pk,
                'form-0-filter_feature_id': ff.pk,
                'form-0-feature': relational.FilterFeature.Expression.AGE,
                'form-0-value': '25',
                'form-0-operator': 'eq',
                'form-0-end_dt': '2010-1-1',
                'form-0-client': self.test_client.pk,
                # Filter Feature 2
                'form-1-filter': self.filter_obj.pk,
                'form-1-filter_feature_id': '',
                'form-1-feature': relational.FilterFeature.Expression.STATE,
                'form-1-value': 'Illinois||Missouri',
                'form-1-operator': 'in',
                'form-1-end_dt': '2010-1-1',
                'form-1-client': self.test_client.pk,
                # Filter Feature 3
                'form-2-filter': self.filter_obj.pk,
                'form-2-filter_feature_id': '',
                'form-2-feature': relational.FilterFeature.Expression.CITY,
                'form-2-value': 'Chicago',
                'form-2-operator': 'eq',
                'form-2-end_dt': '2010-1-1',
                'form-2-client': self.test_client.pk,
                # Filter Feature 4
                'form-3-filter': self.filter_obj.pk,
                'form-3-filter_feature_id': '',
                'form-3-feature': relational.FilterFeature.Expression.GENDER,
                'form-3-value': 'Male',
                'form-3-operator': 'in',
                'form-3-end_dt': '2010-1-1',
                'form-3-client': self.test_client.pk,
                'form-INITIAL_FORMS': 1,
                'form-TOTAL_FORMS': 4,
                'form-MAX_NUM_FORMS': 1000,
            }
        )
        self.assertRedirects(
            response,
            reverse('filter-detail', args=[self.test_client.pk, self.filter_obj.pk])
        )
        filter_obj = self.test_client.filters.get(name='edit_view_test')

        # Filter Changes
        self.assertEqual(filter_obj.description, 'edit view desc')
        self.assertEqual(filter_obj.filterfeatures.count(), 4)
        # Feature Changes
        self.assertTrue(
            filter_obj.filterfeatures.filter(
                value='25', value_type='int').exists()
        )
        self.assertTrue(
            filter_obj.filterfeatures.filter(
                value='Illinois||Missouri', value_type='list').exists()
        )
        self.assertTrue(
            filter_obj.filterfeatures.filter(
                value='Chicago', value_type='string').exists()
        )
        self.assertTrue(
            filter_obj.filterfeatures.filter(
                value='Male', value_type='string').exists()
        )

        for ff in filter_obj.filterfeatures.all():
            self.assertEqual(ff.client, self.test_client)
            if ff.value_type == 'int':
                self.assertTrue(isinstance(ff.decode_value(), (int, long)))
            elif ff.value_type == 'list':
                self.assertTrue(isinstance(ff.decode_value(), list))
            elif ff.value_type == 'float':
                self.assertTrue(isinstance(ff.decode_value(), float))
            elif ff.value_type == 'string':
                self.assertTrue(isinstance(ff.decode_value(), basestring))
            else:
                assert False

    def test_add_filter_feature(self):
        ''' Test ajax view of creating a new filter feature '''
        response = self.client.post(
            reverse('filter-add', args=[self.test_client.pk]), {
                'client': self.test_client.pk,
                'feature': 'state',
                'operator': 'eq',
                'value': 'Wyoming'
            }
        )
        self.assertStatusCode(response, 200)
        data = json.loads(response.content)
        self.assertIn('html', data)
        ff = relational.FilterFeature.objects.get(value='Wyoming')
        self.assertIn(
            'set_number={}.{}.{}'.format(
                ff.feature, ff.operator, ff.value
            ),
            data['html']
        )
