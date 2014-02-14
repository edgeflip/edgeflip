import calendar
import datetime
import time


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


def to_date(epoch):
    """Given seconds since the epoch, return a date."""
    if epoch is None:
        return None
    return datetime.date.fromtimestamp(epoch)


def to_datetime(epoch):
    """Given seconds since the epoch in UTC, return a timezone-aware datetime."""
    if epoch is None:
        return None
    return datetime.datetime.fromtimestamp(epoch, UTC)


def from_date(date):
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


def utcnow():
    return datetime.datetime.utcnow().replace(tzinfo=UTC)
