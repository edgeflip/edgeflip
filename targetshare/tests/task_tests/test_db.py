from django.utils import timezone

from targetshare import models
from targetshare.tasks import db

from .. import EdgeFlipTestCase


class TestDatabaseTasks(EdgeFlipTestCase):

    def test_delayed_bulk_create(self):
        """Task bulk_create calls objects.bulk_create with objects passed"""
        clients = [
            models.relational.Client(
                name="Client {}".format(count),
                codename='client-{}'.format(count)
            )
            for count in xrange(1, 11)
        ]
        client_count = models.relational.Client.objects.count()
        db.bulk_create(clients)
        self.assertEqual(models.relational.Client.objects.count(), client_count + 10)

    def test_delayed_obj_save(self):
        """Task delayed_save calls the save method of the object passed"""
        client = models.relational.Client(name="testy")
        matching_clients = models.relational.Client.objects.filter(name="testy")
        assert not matching_clients.exists()
        db.delayed_save(client)
        assert matching_clients.exists()

    def test_delayed_item_save(self):
        user = models.dynamo.User(fbid=1234)
        self.assertFalse(models.dynamo.User.items.batch_get(keys=[user.get_keys()]))
        db.delayed_save(user)
        self.assertTrue(models.dynamo.User.items.batch_get(keys=[user.get_keys()]))

    def test_delayed_item_save_conflict(self):
        """Dynamo race conditions are caught and data merged"""
        # Provision item:
        alice = models.dynamo.User({
            'fbid': 1234,
            'fname': 'Alice',
            'lname': 'Apples',
            'email': 'aliceapples@yahoo.com',
            'gender': 'Female',
        })
        alice.save()

        # Make changes:
        alice['lname'] = 'Applesauce'
        alice['email'] = 'aliceapplesauce@yahoo.com'

        # Make those changes stale:
        alice_fresh = models.dynamo.User.items.get_item(**alice.get_keys())
        alice_fresh['fname'] = 'Ally'
        alice_fresh['email'] = 'allyapples@yahoo.com'
        alice_fresh.partial_save()

        # Attempt to save stale changes:
        db.partial_save(alice)
        alice_final = models.dynamo.User.items.get_item(**alice.get_keys())
        # Winner of race condition trumps loser:
        self.assertEqual(alice_final['fname'], 'Ally')
        self.assertEqual(alice_final['email'], 'allyapples@yahoo.com')
        # But loser's novel changes make it through:
        self.assertEqual(alice_final['lname'], 'Applesauce')

    def test_delayed_bulk_item_upsert(self):
        # Provision item:
        alice = models.dynamo.User({
            'fbid': 1234,
            'fname': 'Alice',
            'lname': 'Apples',
            'email': 'aliceapples@yahoo.com',
            'gender': 'Female',
            'birthday': timezone.datetime(1945, 4, 14, tzinfo=timezone.utc),
        })
        alice.save()

        # Modify existing item:
        alice['email'] = ''
        alice['fname'] = "Ally"

        # Start new item:
        evan = models.dynamo.User({
            'fbid': 2000,
            'fname': 'Evan',
            'lname': 'Escarole',
            'email': 'evanescarole@hotmail.com',
            'gender': 'Male',
            'birthday': None,
        })

        # Upsert:
        db.upsert([evan, alice])

        alice = models.dynamo.User.items.get_item(**alice.get_keys())
        evan = models.dynamo.User.items.get_item(**evan.get_keys())

        data_a = dict(alice)
        data_a.pop('updated')
        self.assertEqual(data_a, {
            'fbid': 1234,
            'fname': 'Ally', # fname updated
            'lname': 'Apples',
            'email': 'aliceapples@yahoo.com', # Email update ignored (null-y)
            'gender': 'Female',
            'birthday': timezone.datetime(1945, 4, 14, tzinfo=timezone.utc),
        })

        data_e = dict(evan)
        data_e.pop('updated')
        self.assertEqual(data_e, {
            'fbid': 2000,
            'fname': 'Evan',
            'lname': 'Escarole',
            'email': 'evanescarole@hotmail.com',
            'gender': 'Male',
            # birthday ignored
        })
