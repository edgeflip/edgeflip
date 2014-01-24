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
        self.campaign = relational.Campaign.objects.get(pk=1)
        self.client = self.campaign.client
        self.content = relational.ClientContent.objects.get(pk=1)
        self.visit = relational.Visit.objects.create(
            session_id='%s-%s-%s' % (
                datetime.now().strftime('%m-%d-%y_%H:%M:%S'),
                random.randrange(0, 1000),
                random.randrange(0, 1000),
            ),
            app_id=self.client.fb_app_id,
            ip='127.0.0.1',
            source='faces_email',
            visitor=relational.Visitor.objects.create(),
        )
        self.num_face = 3
        self.filename = 'faces_email_test.csv'
        self.notification = relational.Notification.objects.create(
            campaign_id=1, client_content_id=1
        )
        self.notification_user = relational.NotificationUser.objects.create(
            notification=self.notification, fbid=1, uuid='1',
            app_id=self.client.fb_app_id,
        )

    def tearDown(self):
        try:
            os.remove(self.filename)
        except OSError:
            pass

        super(TestFacesEmail, self).tearDown()

    @patch('__builtin__.open')
    @patch('targetshare.management.commands.faces_email.multiprocessing')
    def test_handle(self, mp_mock, open_mock):
        ''' Test to ensure the handle method behaves properly '''
        # Setup Mocks
        write_mock = Mock()
        read_mocks = [Mock(), Mock()]
        open_mock_objs = [write_mock]
        open_mock_objs.extend(read_mocks)
        open_mock.side_effect = open_mock_objs
        pool_mock = Mock()
        pool_mock.map.return_value = ['filename_1', 'filename_2']
        mp_mock.Pool.return_value = pool_mock

        # Add more UserClients
        expires = timezone.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        for x in range(0, 3):
            relational.UserClient.objects.create(
                fbid=x, client=self.client
            )
            token = dynamo.Token(
                fbid=x, appid=self.client.fb_app_id,
                token=x, expires=expires
            )
            token.save()

        # Run the command
        command = faces_email.Command()
        command.handle(
            1, 1, num_face=4, output=self.filename,
            mock=True, url=None, cache=True, offset=0, count=None,
            workers=2
        )

        # Assert lots of things
        self.assertEqual(open_mock.call_count, 3)
        assert write_mock.write.called
        assert write_mock.close.called
        self.assertEqual(
            write_mock.write.call_args_list[0][0][0],
            'primary_fbid,email,friend_fbids,names,html_table\n'
        )
        for x in read_mocks:
            assert x.read.called
        self.assertEqual(relational.Notification.objects.count(), 2)

        assert pool_mock.map.called
        self.assertEqual(
            pool_mock.map.call_args_list[0][0][0],
            faces_email._handle_star_threaded
        )
        self.assertEqual(
            pool_mock.map.call_args_list[0][0][1][0],
            [2L, 1L, 1L, True, 4, 'faces_email_test.csv_part0', None, True, 0, 2]
        )
        self.assertEqual(
            pool_mock.map.call_args_list[0][0][1][1],
            [2L, 1L, 1L, True, 4, 'faces_email_test.csv_part1', None, True, 2, 4]
        )

    @patch('targetshare.management.commands.faces_email.ranking')
    def test_crawl_and_filter(self, ranking_mock):
        ''' Test the _crawl_and_filter method '''
        faces_email._build_csv = Mock()
        expires = timezone.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        for x in range(0, 3):
            relational.UserClient.objects.create(
                fbid=x, client=self.client
            )
            token = dynamo.Token(
                fbid=x, appid=self.client.fb_app_id,
                token=x, expires=expires
            )
            token.save()

        self.command.end_count = None
        edge_data = list(faces_email._crawl_and_filter(
            self.client, self.campaign, self.content,
            self.notification, 0, 100, 3
        ))
        # 4, one is pre-existing from the setUp
        self.assertEqual(
            relational.NotificationUser.objects.count(),
            4
        )
        self.assertEqual(len(edge_data), 3)

    @patch_facebook
    @patch('targetshare.management.commands.faces_email.csv')
    def test_build_csv(self, csv_mock):
        ''' Tests the build_csv method '''
        writer_mock = Mock()
        csv_mock.writer.return_value = writer_mock
        user = facebook.client.get_user(1, 1)
        edge_collection = {
            self.notification_user.uuid: facebook.client.get_friend_edges(user, 1)
        }
        faces_email._build_csv(
            edge_collection.iteritems(), 3, 'faces_email_test.csv',
            self.campaign, self.content, None
        )
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

    @patch_facebook
    @patch('targetshare.management.commands.faces_email.csv')
    def test_build_csv_custom_url(self, csv_mock):
        writer_mock = Mock()
        csv_mock.writer.return_value = writer_mock
        url = 'http://www.google.com'
        user = facebook.client.get_user(1, 1)
        edge_collection = {
            self.notification_user.uuid: facebook.client.get_friend_edges(user, 1)
        }
        faces_email._build_csv(
            edge_collection.iteritems(), 3, 'faces_email_test.csv',
            self.campaign, self.content, url
        )
        assert writer_mock.writerow.called
        assert 'http://www.google.com?efuuid=1' in writer_mock.writerow.call_args[0][0][4]
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
