from django.conf import settings
from django.test import TestCase
from mock import patch
from pymlconf import ConfigDict

from targetshare.models.dynamo import db as dynamo


class EdgeFlipTestCase(TestCase):

    def setUp(self):
        super(EdgeFlipTestCase, self).setUp()

        # Test settings:
        self._main_settings_patch = patch.multiple(
            settings,
            CELERY_ALWAYS_EAGER=True,
            DYNAMO=ConfigDict({'prefix': 'test', 'engine': 'mock', 'port': 4444}),
        )
        self._main_settings_patch.start()

        # Restore dynamo data:
        dynamo.drop_all_tables() # drop if exist
        dynamo.create_all_tables()

    def tearDown(self):
        self._main_settings_patch.stop()
        super(EdgeFlipTestCase, self).tearDown()

    def assertStatusCode(self, response, status=200):
        self.assertEqual(response.status_code, status)
