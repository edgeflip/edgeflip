import json

from django.utils import timezone

from core.utils import classregistry


def decode_date(date):
    if date:
        try:
            (month, day, year) = map(int, date.split('/'))
            return timezone.datetime(year, month, day, tzinfo=timezone.utc)
        except ValueError:
            return None

    return None


class OAuthException(IOError):

    oauth_exception_types = {'OAuthException', 'OAuthBaseException'}
    error_codes = ()

    __metaclass__ = classregistry.AutoRegistering
    _registry_ = {}

    @classmethod
    def __register__(cls):
        for code in cls.error_codes:
            cls._registry_[code] = cls

    @classmethod
    def is_oauth_exception(cls, msg):
        try:
            response = json.loads(msg)
            error_type = response['error']['type']
            error_code = response['error']['code']
        except (KeyError, ValueError):
            return (False, None)
        else:
            return (error_type in cls.oauth_exception_types, error_code)

    @classmethod
    def raise_for_response(cls, msg):
        (is_oauth, error_code) = cls.is_oauth_exception(msg)
        if is_oauth:
            subclass = cls._registry_.get(error_code, cls)
            raise subclass(msg)


class OAuthTooManyCalls(OAuthException):
    pass


class OAuthTooManyAppCalls(OAuthTooManyCalls):

    error_codes = (4,)


class OAuthTooManyUserCalls(OAuthTooManyCalls):

    error_codes = (17,)


class OAuthTokenExpired(OAuthException):

    error_codes = (102,)


class OAuthPermissionDenied(OAuthException):

    error_codes = (10,)

    unapproved_snippet = "your use of this endpoint must be reviewed and approved by Facebook"

    @property
    def requires_review(self):
        return self.unapproved_snippet in self.message
