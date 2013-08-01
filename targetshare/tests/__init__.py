from django.test import TestCase


class EdgeFlipTestCase(TestCase):

    def setUp(self):
        super(EdgeFlipTestCase, self).setUp()

    def tearDown(self):
        super(EdgeFlipTestCase, self).setUp()

    def assertStatusCode(self, response, status=200):
        self.assertEqual(response.status_code, status)

from .test_views import TestEdgeFlipViews
