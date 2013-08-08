from django.test import TestCase
from django.conf import settings


class EdgeFlipTestCase(TestCase):

    def setUp(self):
        super(EdgeFlipTestCase, self).setUp()
        self.eager = settings.CELERY_ALWAYS_EAGER
        settings.CELERY_ALWAYS_EAGER = True

    def tearDown(self):
        settings.CELERY_ALWAYS_EAGER = self.eager
        super(EdgeFlipTestCase, self).tearDown()

    def assertStatusCode(self, response, status=200):
        self.assertEqual(response.status_code, status)
