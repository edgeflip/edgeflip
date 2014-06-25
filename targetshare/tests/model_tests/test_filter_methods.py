from datetime import datetime
from decimal import Decimal

import mock
from freezegun import freeze_time

from targetshare import models

from .. import EdgeFlipTestCase


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

    def _operate(self, feature, operator, value, feature_code=None):
        feature_code = feature_code or feature
        (feature_type,
         _created) = models.FilterFeatureType.objects.get_or_create(code=feature_code)
        feature = models.FilterFeature(
            filter=self.filter,
            feature=feature,
            feature_type=feature_type,
            operator=operator,
            value=value,
        )
        (feature.value, feature.value_type) = feature.encode_value()
        return feature.operate_standard(self.user)

    def assertFilter(self, feature, operator, value, feature_code=None):
        self.assertTrue(self._operate(feature, operator, value, feature_code))

    def assertNotFilter(self, feature, operator, value, feature_code=None):
        self.assertFalse(self._operate(feature, operator, value, feature_code))

    def test_standard_filter_age(self):
        self.assertFilter(self.expressions.AGE, self.operators.MIN, 10)
        self.assertFilter(self.expressions.AGE, self.operators.MAX, 50)
        self.assertFilter(self.expressions.AGE, self.operators.EQ, 29)

        # list of non-strings currently unsupported:
        self.assertNotFilter(self.expressions.AGE, self.operators.IN, [10, 29, 50])
        age = models.dynamo.User.age.fget # property's getter
        str_age = lambda: str(age(self.user))
        property_mock = mock.PropertyMock(side_effect=str_age)
        with mock.patch.object(models.dynamo.User, 'age', new_callable=property_mock):
            self.assertEqual(self.user.age, '29')
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

    def test_standard_filter_topics(self):
        topics_type = models.FilterFeatureType.TOPICS
        self.assertEqual(self.user.topics, {})
        self.assertNotFilter('topics[Sports]', self.operators.MAX, '0.99', topics_type)
        delattr(self.user, 'topics') # Clear cache

        models.PostTopics.items.create(
            postid='1_1',
            classifier=models.PostTopics.QD_CLASSIFIER,
            Health=Decimal('1.2'),
            Sports=Decimal('5.0'),
        )
        models.PostInteractions.items.create(
            user=self.user,
            postid='1_1',
            post_likes=1,
            post_comms=2,
            tags=1,
        )
        self.assertEqual(self.user.topics, {
            # Normalized values:
            'Health': 0.7486681672439952,
            'Sports': 0.936548965138893,
        })

        self.assertFilter('topics[Health]', self.operators.MIN, '0.7', topics_type)
        self.assertFilter('topics[Sports]', self.operators.MAX, '0.99', topics_type)
        self.assertNotFilter('topics[Sports]', self.operators.MAX, '0.93', topics_type)

    def test_standard_filter_missing_feature(self):
        self.assertNotFilter('not_an_option', self.operators.EQ, 1000)
