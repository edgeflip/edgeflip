from targetshare.tests import EdgeFlipTestCase
from targetshare.models import relational


class TestAdminBase(EdgeFlipTestCase):

    def setUp(self):
        super(TestAdminBase, self).setUp()
        self.test_client = relational.Client.objects.get(pk=1)
        self.test_content = relational.ClientContent.objects.create(
            name='Testing Content',
            client=self.test_client
        )
        assert self.client.login(
            username='tester',
            password='testing',
        )
