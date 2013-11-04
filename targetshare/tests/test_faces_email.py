import os
import random
from datetime import datetime

from mock import Mock, patch

from django.utils import timezone

from targetshare.integration import facebook
from targetshare.models import dynamo, relational
from targetshare.management.commands import faces_email

from . import EdgeFlipTestCase, patch_facebook


class TestFacesEmail(EdgeFlipTestCase):

    fixtures = ['test_data']

    def setUp(self):
        super(TestFacesEmail, self).setUp()
        self.command = faces_email.Command()
        self.command.mock = True
        self.command.campaign = relational.Campaign.objects.get(pk=1)
        self.command.client = self.command.campaign.client
        self.command.content = relational.ClientContent.objects.get(pk=1)
        self.command.visit = relational.Visit.objects.create(
            session_id='%s-%s-%s' % (
                datetime.now().strftime('%m-%d-%y_%H:%M:%S'),
                random.randrange(0, 1000),
                random.randrange(0, 1000),
            ),
            app_id=self.command.client.fb_app_id,
            ip='127.0.0.1',
            source='faces_email',
            visitor=relational.Visitor.objects.create(),
        )
        self.command.num_face = 3
        self.command.filename = 'faces_email_test.csv'
        self.command.task_list = {}
        self.command.edge_collection = {}
        self.command.csv_writer = Mock()
        self.command.file_handle = Mock()
        self.command.failed_fbids = []
        self.command.cache = True
        self.command.offset = 0
        self.notification = relational.Notification.objects.create(
            campaign_id=1, client_content_id=1
        )
        self.command.notification = self.notification
        self.notification_user = relational.NotificationUser.objects.create(
            notification=self.notification, fbid=1, uuid='1',
            app_id=self.command.client.fb_app_id,
        )

    def tearDown(self):
        try:
            os.remove(self.command.filename)
        except OSError:
            pass

        super(TestFacesEmail, self).tearDown()

    def test_handle(self):
        ''' Test to ensure the handle method behaves properly '''
        command = faces_email.Command()
        methods_to_mock = [
            '_build_csv',
        ]
        pre_mocks = []
        for method in methods_to_mock:
            pre_mocks.append(getattr(command, method))
            setattr(command, method, Mock())

        command.handle(
            1, 1, num_face=4, output='testing.csv',
            mock=True, url=None, cache=True, offset=0, count=None
        )
        for count, method in enumerate(methods_to_mock):
            assert getattr(command, method).called
            setattr(command, method, pre_mocks[count])

        self.assertEqual(command.campaign.pk, 1)
        self.assertEqual(command.content.pk, 1)
        assert self.command.mock
        self.assertEqual(command.num_face, 4)
        self.assertEqual(command.filename, 'testing.csv')
        # 1 we created in setUp, the other the command did
        self.assertEqual(relational.Notification.objects.count(), 2)

    @patch('targetshare.management.commands.faces_email.ranking')
    def test_crawl_and_filter(self, ranking_mock):
        ''' Test the _crawl_and_filter method '''
        self.command._build_csv = Mock()
        expires = timezone.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        for x in range(0, 3):
            relational.UserClient.objects.create(
                fbid=x, client=self.command.client
            )
            token = dynamo.Token(
                fbid=x, appid=self.command.client.fb_app_id,
                token=x, expires=expires
            )
            token.save()

        self.command.end_count = None
        edge_data = list(self.command._crawl_and_filter())
        # 4, one is pre-existing from the setUp
        self.assertEqual(
            relational.NotificationUser.objects.count(),
            4
        )
        self.assertEqual(len(edge_data), 3)

    @patch_facebook
    def test_build_csv(self):
        ''' Tests the build_csv method '''
        user = facebook.client.get_user(1, 1)
        self.command.edge_collection = {
            self.notification_user.uuid: facebook.client.get_friend_edges(user, 1)
        }
        self.command.url = None
        self.command._build_csv(self.command.edge_collection.iteritems())
        assert self.command.csv_writer.writerow.called
        assert self.command.csv_writer.writerow.call_args[0][0][4].strip().startswith('<table')
        self.assertEqual(
            self.command.csv_writer.writerow.call_args[0][0][1],
            'fake@fake.com'
        )
        self.assertEqual(
            relational.NotificationEvent.objects.filter(
                event_type='shown').count(),
            3
        )
        assert relational.NotificationEvent.objects.filter(
            event_type='generated').exists()

    @patch_facebook
    def test_build_csv_custom_url(self):
        self.command.url = 'http://www.google.com'
        user = facebook.client.get_user(1, 1)
        self.command.edge_collection = {
            self.notification_user.uuid: facebook.client.get_friend_edges(user, 1)
        }
        self.command._build_csv(self.command.edge_collection.iteritems())
        assert self.command.csv_writer.writerow.called
        assert 'http://www.google.com?efuuid=1' in self.command.csv_writer.writerow.call_args[0][0][4]
        self.assertEqual(
            self.command.csv_writer.writerow.call_args[0][0][1],
            'fake@fake.com'
        )
        self.assertEqual(
            relational.NotificationEvent.objects.filter(
                event_type='shown').count(),
            3
        )
        assert relational.NotificationEvent.objects.filter(
            event_type='generated').exists()
