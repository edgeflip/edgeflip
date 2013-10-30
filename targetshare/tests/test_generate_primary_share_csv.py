import os
import random
from datetime import datetime
from decimal import Decimal

from mock import Mock, patch

from targetshare.models import dynamo, relational
from targetshare.management.commands import generate_primary_share_csv

from . import EdgeFlipTestCase


class TestGeneratePrimaryShareCSV(EdgeFlipTestCase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestGeneratePrimaryShareCSV, self).setUp()
        self.command = generate_primary_share_csv.Command()
        self.visit = relational.Visit.objects.create(
            session_id='%s-%s-%s' % (
                datetime.now().strftime('%m-%d-%y_%H:%M:%S'),
                random.randrange(0, 1000),
                random.randrange(0, 1000),
            ),
            app_id=12345,
            ip='127.0.0.1',
            source='faces_email',
            visitor=relational.Visitor.objects.create(fbid=12345),
        )

    def tearDown(self):
        if hasattr(self.command, 'file_handle'):
            try:
                os.remove(self.command.file_handle.name)
            except OSError:
                pass

        super(TestGeneratePrimaryShareCSV, self).tearDown()

    @patch('targetshare.management.commands.generate_primary_share_csv.csv')
    def test_generating_primary_share_csv(self, csv_mock):
        writer_mock = Mock()
        csv_mock.writer.return_value = writer_mock
        self.visit.events.create(
            campaign_id=1, event_type='shared'
        )
        user = dynamo.User(
            fbid=12345, email='test@testing.com', fname='test', lname='test'
        )
        user.save()
        self.command.handle(1, output='testing.csv')
        assert writer_mock.writerow.called
        self.assertEqual(
            writer_mock.writerow.call_args[0],
            ([Decimal('12345'), 'test@testing.com'],)
        )
