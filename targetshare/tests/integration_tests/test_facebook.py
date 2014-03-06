import unittest

from django.utils import timezone

from targetshare.integration import facebook


class TestFacebookIntegration(unittest.TestCase):

    def test_decode_date_valid(self):
        bday = facebook.client.decode_date('02/01/2000')
        self.assertEqual(
            bday,
            timezone.datetime(2000, 2, 1, tzinfo=timezone.utc)
        )

    def test_decode_date_invalid_leap_year(self):
        bday = facebook.client.decode_date('02/29/1905')
        self.assertEqual(bday, None)

    def test_decode_date_valid_leap_year(self):
        bday = facebook.client.decode_date('02/29/2004')
        self.assertEqual(
            bday,
            timezone.datetime(2004, 2, 29, tzinfo=timezone.utc)
        )

    def test_decode_date_invalid_string(self):
        bday = facebook.client.decode_date('02/29/AAAA')
        self.assertEqual(bday, None)
