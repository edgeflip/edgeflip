from datetime import datetime

from freezegun import freeze_time

from targetshare import models

from . import EdgeFlipTestCase


@freeze_time('2013-01-01')
class TestFilters(EdgeFlipTestCase):

    fixtures = ['test_data']
    expressions = models.FilterFeature.Expression
    operators = models.FilterFeature.Operator

    def setUp(self):
        super(TestFilters, self).setUp()
        self.client = models.Client.objects.get(pk=1)
        self.filter = models.Filter.objects.create(
            name='test filter',
            client=self.client
        )
        self.user = models.User(
            fbid=1,
            birthday=datetime(1984, 1, 1),
            fname='test',
            lname='user',
            gender='male',
            city='Chicago',
            state='Illinois',
            country='United States'
        )

    def _operate(self, feature, operator, value):
        feature_type, _created = models.FilterFeatureType.objects.get_or_create(code=feature)
        feature = models.FilterFeature(
            filter=self.filter,
            feature=feature,
            feature_type=feature_type,
            operator=operator,
            value=value,
        )
        return feature.operate_standard(self.user)

    def assertFilter(self, feature, operator, value):
        self.assertTrue(self._operate(feature, operator, value))

    def assertNotFilter(self, feature, operator, value):
        self.assertFalse(self._operate(feature, operator, value))

    def test_standard_filter_age(self):
        self.assertFilter(self.expressions.AGE, self.operators.MIN, 10)
        self.assertFilter(self.expressions.AGE, self.operators.MAX, 50)
        self.assertFilter(self.expressions.AGE, self.operators.EQ, 29)
        self.assertFilter(self.expressions.AGE, self.operators.IN, [10, 29, 50])

    def test_standard_filter_gender(self):
        self.assertFilter(self.expressions.GENDER, self.operators.EQ, 'male')
        self.assertNotFilter(self.expressions.GENDER, self.operators.EQ, 'female')

    def test_standard_filter_state(self):
        self.assertFilter(self.expressions.STATE, self.operators.EQ, 'Illinois')
        self.assertFilter(self.expressions.STATE, self.operators.IN, ['Illinois', 'Missouri'])

    def test_standard_filter_city(self):
        self.assertFilter(self.expressions.CITY, self.operators.EQ, 'Chicago')
        self.assertFilter(self.expressions.CITY, self.operators.IN, ['Chicago', 'Fenton'])

    def test_standard_filter_full_location(self):
        locations = (
            'Chicago, Illinois United States',
            'St. Louis, Missouri United States',
        )
        self.assertFilter(self.expressions.FULL_LOCATION, self.operators.EQ, locations[0])
        self.assertFilter(self.expressions.FULL_LOCATION, self.operators.IN, locations)

    def test_standard_filter_missing_feature(self):
        self.assertNotFilter('not_an_option', self.operators.EQ, 1000)
