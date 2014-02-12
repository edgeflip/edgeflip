from targetshare.tests import EdgeFlipTestCase
from targetshare.models import relational


class TestReportingBase(EdgeFlipTestCase):

    fixtures = ['reporting_testdata', 'redshift_testdata']
    multi_db = True

    def login_superuser(self):
        assert(self.client.login(
            username='potus',
            password='testing'
        ))

    def login_clientuser(self):
        assert(self.client.login(
            username='peon',
            password='testing'
        ))

