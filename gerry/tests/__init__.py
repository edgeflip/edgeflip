import faraday
from mock import patch


class GerryTestCase(object):

    global_patches = (
        patch.multiple(
            faraday.conf.settings,
            PREFIX='test',
            LOCAL_ENDPOINT='localhost:4444',
        ),
    )

    @classmethod
    def setUpClass(cls):
        for patch_ in cls.global_patches:
            patch_.start()

        # In case a bad test class doesn't clean up after itself:
        faraday.db.destroy()

    @classmethod
    def tearDownClass(cls):
        for patch_ in cls.global_patches:
            patch_.stop()

    def setUp(self):
        faraday.db.build()

    def tearDown(self):
        faraday.db.destroy()
