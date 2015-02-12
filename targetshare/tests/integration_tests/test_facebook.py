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
        facebook.utils.OAuthException.raise_for_response('garbage')

        with self.assertRaises(facebook.utils.OAuthTooManyAppCalls):
            facebook.utils.OAuthException.raise_for_response(
                '{"error": {"message": "Expired token or somesuch","type": "OAuthException","code": 4}}'
            )

        with self.assertRaises(facebook.utils.OAuthPermissionDenied):
            facebook.utils.OAuthException.raise_for_response(
                '{"error": {"message": "Expired token or somesuch","type": "OAuthException","code": 10}}'
            )
