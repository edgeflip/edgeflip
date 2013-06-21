import os
import mock
import unittest

from edgeflip.web import getApp
from edgeflip.settings import config
from edgeflip import database, client_db_reset as cdbr

APP = getApp()
REPO_ROOT = os.path.join(os.path.dirname(__file__), '../', '../')


class EdgeFlipTestCase(unittest.TestCase):
    ''' The start of our base testing class '''

    def setUp(self):
        ''' This is a bit on the crazy side, using popen to construct and
        destroy out database. Hopefully can find something better, but
        currently flask and our database are very separated which makes testing
        a bit on the interesting side.
        '''
        APP.config['TESTING'] = True
        config.dbname = 'edgeflip_test'
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
        database.dbSetup()
        cdbr.client_db_reset()
        self.conn = database.getConn()
        self.conn.begin()
        self.conn.commit = mock.Mock()
        db_mock = mock.Mock(return_value=self.conn)
        self.getConn = database.getConn
        database.getConn = db_mock

    def tearDown(self):
        ''' Be a good neighbor, clean up after yourself. '''
        import ipdb; ipdb.set_trace() ### XXX BREAKPOINT
        self.conn.rollback()
        self.conn.close()
        database.getConn = self.getConn
        os.popen(
            'mysqladmin -uroot -proot drop edgeflip_test -f'
        ).read()
        config.dbname = 'edgeflip'
