import random
from datetime import datetime

from mock import Mock, patch

from django.utils import timezone
from django.utils.datastructures import SortedDict

from targetshare.integration.facebook import mock_client
from targetshare.models import dynamo, relational
from targetshare.management.commands import faces_email

from . import EdgeFlipTestCase


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
            fbid=None,
            source='faces_email',
        )
        self.command.num_face = 3
        self.command.filename = 'faces_email_test.csv'
        self.command.task_list = {}
        self.command.edge_collection = {}
        self.notification = relational.Notification.objects.create(
            campaign_id=1, client_content_id=1
        )
        self.command.notification = self.notification
        self.notification_user = relational.NotificationUser.objects.create(
            notification=self.notification, fbid=1, uuid='1',
            app_id=self.command.client.fb_app_id,
        )

    def test_handle(self):
        ''' Test to ensure the handle method behaves properly '''
        command = faces_email.Command()
        methods_to_mock = [
            '_crawl_and_filter',
            '_crawl_status_handler',
            '_build_csv',
        ]
        pre_mocks = []
        for method in methods_to_mock:
            pre_mocks.append(getattr(command, method))
            setattr(command, method, Mock())

        command.handle(
            1, 1, num_face=4, output='testing.csv', mock=True
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

        self.command._crawl_and_filter()
        assert ranking_mock.proximity_rank_three.called
        self.assertEqual(ranking_mock.proximity_rank_three.call_count, 3)
        self.assertEqual(len(self.command.task_list), 3)

    def test_crawl_status_handler(self):
        ''' Tests the _crawl_status_handler method '''
        good_result = Mock()
        good_result.ready.return_value = True
        good_result.successful.return_value = True
        good_result.result = ['', Mock(edges=[1, 2, 3])]

        bad_result = Mock()
        bad_result.ready.return_value = True
        bad_result.successful.return_value = False
        bad_result.result = ['', 'bad_result']

        pending_result = Mock()
        pending_result.ready.return_value = False
        pending_result.successful.return_value = False
        parent_mock = Mock()
        parent_mock.ready.return_value = True
        parent_mock.successful.return_value = False
        pending_result.parent = parent_mock

        self.command.task_list = SortedDict({
            self.notification_user.uuid: good_result,
            '2': bad_result,
            '3': pending_result,
        })
        self.command._crawl_status_handler()

        self.assertEqual(
            self.command.edge_collection,
            {self.notification_user.uuid: [1, 2, 3]}
        )

    @patch('targetshare.management.commands.faces_email.csv')
    def test_build_csv(self, csv_mock):
        ''' Tests the build_csv method '''
        writer_mock = Mock()
        csv_mock.writer.return_value = writer_mock
        self.command.edge_collection = {
            self.notification_user.uuid: mock_client.getFriendEdgesFb(1, 1)
        }
        self.command._build_csv()
        assert writer_mock.writerow.called
        assert writer_mock.writerow.call_args[0][0][4].strip().startswith('<table')
        self.assertEqual(
            writer_mock.writerow.call_args[0][0][1],
            'fake@fake.com'
        )
        self.assertEqual(
            relational.NotificationEvent.objects.filter(
                event_type='shown').count(),
            3
        )
        assert relational.NotificationEvent.objects.filter(
            event_type='generated').exists()
