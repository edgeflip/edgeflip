from django.test import TestCase


class EdgeFlipTestCase(TestCase):

    def assertStatusCode(self, response, status=200):
        self.assertEqual(response.status_code, status)

