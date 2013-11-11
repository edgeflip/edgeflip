from datetime import datetime

from freezegun import freeze_time

from targetshare import models

from . import EdgeFlipTestCase


@freeze_time('2013-01-01')
class TestFilters(EdgeFlipTestCase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestFilters, self).setUp()
        self.client = models.Client.objects.get(pk=1)
        self.filter_obj = models.Filter.objects.create(
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

    def test_standard_filter_age(self):
        self.assertTrue(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeature.AGE, 'min', 10)
        )
        self.assertTrue(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeature.AGE, 'max', 50)
        )
        self.assertTrue(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeature.AGE, 'eq', 29)
        )
        self.assertTrue(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeature.AGE, 'in', [10, 29, 50])
        )

    def test_standard_filter_gender(self):
        self.assertTrue(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeature.GENDER, 'eq', 'male')
        )
        self.assertFalse(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeature.GENDER, 'eq', 'female')
        )

    def test_standard_filter_state(self):
        self.assertTrue(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeature.STATE, 'eq', 'Illinois')
        )
        self.assertTrue(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeature.STATE, 'in', ['Illinois', 'Missouri'])
        )

    def test_standard_filter_city(self):
        self.assertTrue(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeature.CITY, 'eq', 'Chicago')
        )
        self.assertTrue(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeature.CITY, 'in', ['Chicago', 'Fenton'])
        )

    def test_standard_filter_full_location(self):
        locations = [
            'Chicago, Illinois United States',
            'St. Louis, Missouri United States',
        ]
        self.assertTrue(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeatureType.FULL_LOCATION, 'eq', locations[0])
        )
        self.assertTrue(
            self.filter_obj._standard_filter(
                self.user, models.FilterFeatureType.FULL_LOCATION, 'in', locations)
        )

    def test_standard_filter_missing_feature(self):
        self.assertFalse(
            self.filter_obj._standard_filter(
                self.user, 'not_an_option', 'eq', 1000)
        )
