from targetshare.tests import EdgeFlipTestCase
from targetshare.models import relational


class TestAdminBase(EdgeFlipTestCase):

    def setUp(self):
        super(TestAdminBase, self).setUp()
        self.test_client = relational.Client.objects.create(
            name='Testing Client',
            _fb_app_id=1234,
            _fb_app_name='That One App',
            domain='example.com',
            subdomain='test',
        )
        self.test_content = relational.ClientContent.objects.create(
            name='Testing Content',
            client=self.test_client
        )
        assert self.client.login(
            username='tester',
            password='testing',
        )
