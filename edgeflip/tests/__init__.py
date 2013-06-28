import os
import unittest

from edgeflip.web import getApp
from edgeflip.settings import config
from edgeflip import database

APP = getApp()
REPO_ROOT = os.path.join(os.path.dirname(__file__), '../', '../')


class EdgeFlipTestCase(unittest.TestCase):
    ''' The start of our base testing class '''

    def setUp(self):
        ''' This is a bit on the crazy side, using popen to construct and
        destroy our database. Hopefully can find something better, but
        currently flask and our database are very separated which makes testing
        a bit on the interesting side.
        '''
        APP.config['TESTING'] = True
        self.orig_dbname = config.dbname
        self.orig_dbuser = config.dbuser
        self.orig_eager = config.always_eager
        config.always_eager = True
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
            'mysql -uroot -proot < %s/sql/initial_test.sql' % REPO_ROOT
        ).read()
        os.popen(
            'mysql -uroot -proot edgeflip_test < %s/sql/test_database.sql' % REPO_ROOT
        ).read()
        self.conn = database.getConn()

    def tearDown(self):
        ''' Be a good neighbor, clean up after yourself. '''
        self.conn.close()
        config.always_eager = self.orig_eager
        config.dbname = self.orig_dbname
        config.dbuser = self.orig_dbuser
