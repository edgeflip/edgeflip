import os
import unittest

from edgeflip.web import getApp
from edgeflip.settings import config
from edgeflip import database
from edgeflip.celery import celery

APP = getApp()
FILE_ROOT = os.path.dirname(__file__)


class EdgeFlipTestCase(unittest.TestCase):
    ''' The start of our base testing class '''

    def setUp(self):
        ''' This is a bit on the crazy side, using popen to construct and
        destroy our database. Hopefully can find something better, but
        currently flask and our database are very separated which makes testing
        a bit on the interesting side.
        '''
        super(EdgeFlipTestCase, self).setUp()
        # APP Adjustments
        APP.config['TESTING'] = True

        # Celery Adjustments
        self.orig_eager = celery.conf['CELERY_ALWAYS_EAGER']
        celery.conf['CELERY_ALWAYS_EAGER'] = True

        # Database Adjustments
        self.orig_dbname = config.dbname
        self.orig_dbuser = config.dbuser
        config.dbname = 'edgeflip_test'
        config.dbuser = 'edgeflip_test'
        config.unit_testing = True

        self.app = APP.test_client()
        # Let's drop the test database, just in case the last run failed
        os.popen(
            'mysqladmin -uroot -proot drop edgeflip_test -f'
        ).read()
        # Now let's create the database
        os.popen(
            'mysql -uroot -proot < %s/test_data/initial_test.sql' % FILE_ROOT
        ).read()
        os.popen(
            'mysql -uroot -proot edgeflip_test < %s/test_data/test_database.sql' % FILE_ROOT
        ).read()
        self.conn = database.getConn()

    def tearDown(self):
        ''' Be a good neighbor, clean up after yourself. '''
        self.conn.close()
        celery.conf['CELERY_ALWAYS_EAGER'] = self.orig_eager
        config.dbname = self.orig_dbname
        config.dbuser = self.orig_dbuser
        super(EdgeFlipTestCase, self).tearDown()

    def assertStatusCode(self, response, status=200):
        self.assertEqual(response.status_code, status)


class EdgeFlipFlaskTestCase(unittest.TestCase):

    def setUp(self):
        super(EdgeFlipFlaskTestCase, self).setUp()

    def tearDown(self):
        super(EdgeFlipFlaskTestCase, self).tearDown()
