import json

from django.utils import timezone


def decode_date(date):
    if date:
        try:
            (month, day, year) = map(int, date.split('/'))
            return timezone.datetime(year, month, day, tzinfo=timezone.utc)
        except ValueError:
            return None

    return None


OAUTH_EXCEPTION_TYPES = {
    'OAuthException',
    'OAuthBaseException',
}


class OAuthException(IOError):

    @staticmethod
    def is_oauth_exception(msg):
        try:
            response = json.loads(msg)
            return (
                response['error']['type'] in OAUTH_EXCEPTION_TYPES and
                'Application request limit reached' not in response['error']['message']
            )
        except (KeyError, ValueError):
            return False

    @classmethod
    def raise_for_response(cls, msg):
        if cls.is_oauth_exception(msg):
            raise cls(msg)
