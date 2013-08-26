import mock
from django.conf import settings
from django.test import TestCase
from pymlconf import ConfigDict

from targetshare.models.dynamo import utils


class EdgeFlipTestCase(TestCase):

    def setUp(self):
        super(EdgeFlipTestCase, self).setUp()

        # Test settings:
        self.patches = []
        self.patches.append(
            mock.patch.multiple(
                settings,
                CELERY_ALWAYS_EAGER=True,
                DYNAMO=ConfigDict({'prefix': 'test', 'engine': 'mock', 'port': 4444}),
            )
        )
        # Dynamo tables are created eagerly; force reset of prefix:
        for table in utils.database.tables:
            self.patches.append(
                mock.patch.object(table, 'table_name', table.short_name)
            )
        # Start patches:
        for patch in self.patches:
            patch.start()

        # Restore dynamo data:
        utils.database.drop_all_tables() # drop if exist
        utils.database.create_all_tables()

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        super(EdgeFlipTestCase, self).tearDown()

    def assertStatusCode(self, response, status=200):
        self.assertEqual(response.status_code, status)
