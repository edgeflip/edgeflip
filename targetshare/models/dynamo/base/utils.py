import calendar
import datetime
import logging
import re
import time
from StringIO import StringIO

from . import conf


LOG = logging.getLogger(conf.settings.LOGGER)


class cached_property(object):
    """property-like descriptor, which caches its result in instance dictionary."""

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        result = vars(instance)[self.func.__name__] = self.func(instance)
        return result


def camel_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class DummyIO(StringIO):

    def write(self, _buffer):
        pass

    def flush(self):
        pass

dummyio = DummyIO()


class Utc(datetime.tzinfo):
    """UTC implementation taken from Python's docs (taken from django.utils.timezone).

    """
    ZERO = datetime.timedelta(0)

    def __repr__(self):
        return "<UTC>"

    def utcoffset(self, dt):
        return self.ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return self.ZERO

UTC = Utc()


def epoch_to_date(epoch):
    """Given seconds since the epoch, return a date."""
    if epoch is None:
        return None
    return datetime.date.fromtimestamp(epoch)


def epoch_to_datetime(epoch):
    """Given seconds since the epoch in UTC, return a timezone-aware datetime."""
    if epoch is None:
        return None
    return datetime.datetime.fromtimestamp(epoch, UTC)


def to_epoch(date):
    """Given a datetime.date or datetime.datetime, return seconds since the
    epoch in UTC.

    """
    if date is None:
        return None
    if isinstance(date, datetime.datetime):
        # Handle datetime timezones:
        return calendar.timegm(date.utctimetuple())
    # Naively convert time-less date:
    return time.mktime(date.timetuple())


def now():
    return datetime.utcnow().replace(tzinfo=UTC)
