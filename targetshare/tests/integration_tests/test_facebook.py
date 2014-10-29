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

    def test_decode_date_missing_data(self):
        ''' Facebook can't always provide us with the year someone was born '''
        bday = facebook.client.decode_date('02/29')
        self.assertEqual(bday, None)

    def test_is_oauth_exception(self):
        exceptions = {
            '{"error": {"message": "(#4) Application request limit reached","type": "OAuthException","code": 4}}': False,
            '{"error": {"message": "Expired token or somesuch","type": "OAuthException","code": 4}}': True,
            'garbage': False,
        }

        for exception, is_oauth in exceptions.iteritems():
            self.assertEqual(
                facebook.client.is_oauth_exception(exception),
                is_oauth
            )
