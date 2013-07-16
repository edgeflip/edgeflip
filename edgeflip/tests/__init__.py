import os
import mock
import unittest
from subprocess import call, PIPE

from edgeflip.web import getApp
from edgeflip.settings import config
from edgeflip import database
from edgeflip.celery import celery

APP = getApp()
FILE_ROOT = os.path.dirname(__file__)


def setUp(self):
    ''' Package level setUp method. This should only handle items that need
    to be built for the entire test suite to be able to run. For now, that
    simply creates the database.

    This method is ran *once* per test suite run
    '''
    # Let's drop the test database, just in case the last run failed
    call(
        '/usr/bin/mysqladmin -uroot -proot -f drop edgeflip_test',
        shell=True, stderr=PIPE, stdout=PIPE
    )
    # Now let's create the database
    call('/usr/bin/mysql -uroot -proot < edgeflip/tests/test_data/initial_test.sql', shell=True)
    call('/usr/bin/mysql -uroot -proot edgeflip_test < %s/test_data/test_database.sql' % (
        FILE_ROOT
    ), shell=True)


def tearDown(self):
    ''' Package level tearDown method. This will run after all of the tests
    in the given suite have ran.
    '''
    call(
        '/usr/bin/mysqladmin -uroot -proot -f drop edgeflip_test',
        shell=True, stderr=PIPE, stdout=PIPE
    )


class EdgeFlipTestCase(unittest.TestCase):
    ''' The start of our base testing class '''

    def setUp(self):
        ''' Performs a lot of the necessary setup for testing the edgeflip
        application. That setup involves:

            * Sets the Flask app into a testing mode, and grabs the Flask test
            client for making test API requests.
            * Dummies out config values for the database.
            * Puts celery into "eager" mode, which means that tasks are handled
            in process rather than through the queues.
            * Mocks out the commit functionality of the database connection,
            so that we can simply rollback all of our queries rather than
            building/destroying the database on each test run
        '''
        super(EdgeFlipTestCase, self).setUp()
        # APP Adjustments
        APP.config['TESTING'] = True
        self.app = APP.test_client()
        config.unit_testing = True

        # Celery Adjustments
        self.orig_eager = celery.conf['CELERY_ALWAYS_EAGER']
        celery.conf['CELERY_ALWAYS_EAGER'] = True

        # Database Adjustments
        self.orig_dbname = config.dbname
        self.orig_dbuser = config.dbuser
        config.dbname = 'edgeflip_test'
        config.dbuser = 'edgeflip_test'

        # Prevent commits to the database
        self.conn = database.getConn()
        self.conn.begin()
        self.orig_commit = self.conn.commit
        self.conn.commit = mock.Mock()

        # Mock the getConn call to always return the same connection
        db_mock = mock.Mock(return_value=self.conn)
        self.getConn = database.getConn
        database.getConn = db_mock

    def tearDown(self):
        ''' Be a good neighbor, clean up after yourself. '''
        # Return the commit function and rollback our open transaction
        self.conn.commit = self.orig_commit
        self.conn.rollback()
        self.conn.close()

        # Return the getConn method
        database.getConn = self.getConn

        # Put settings back into place
        celery.conf['CELERY_ALWAYS_EAGER'] = self.orig_eager
        config.dbname = self.orig_dbname
        config.dbuser = self.orig_dbuser

        # Undo APP settings
        APP.config['TESTING'] = False
        config.unit_testing = False
        super(EdgeFlipTestCase, self).tearDown()

    def assertStatusCode(self, response, status=200):
        self.assertEqual(response.status_code, status)