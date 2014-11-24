import functools

from django.conf import settings
from django.db import connections, DatabaseError, DEFAULT_DB_ALIAS


def lock(*args, **kws):
    if args and callable(args[0]):
        # Use as decorator: @lock
        # -- (but for debugging/etc. we'll pass along remaining args)
        decorated = args[0]
        if len(args) == 1 and 'nickname' not in kws and 'fullname' not in kws:
            # No name specified, use callable's
            # TODO: Use full module path?
            kws['nickname'] = decorated.__name__
        return AdvisoryLock(*args[1:], **kws)(decorated)

    # Args configure decorator / context manager object
    return AdvisoryLock(*args, **kws)


class LockError(DatabaseError):
    pass


class AcquisitionFailure(LockError):
    pass


class TimeoutError(AcquisitionFailure):
    pass


class ReleaseFailure(LockError):
    pass


class AdvisoryLock(object):

    DEFAULT_TIMEOUT = 3

    def __init__(self, nickname=None, fullname=None, using=None, timeout=None):
        if (nickname is None and fullname is None) or (nickname is not None and fullname is not None):
            raise TypeError("either nickname or fullname required")
        self.nickname = nickname
        self._fullname = fullname
        self._prefix = None

        self.using = DEFAULT_DB_ALIAS if using is None else using
        if timeout is None:
            self.timeout = getattr(settings, 'ADVISORY_LOCK_DEFAULT_TIMEOUT', self.DEFAULT_TIMEOUT)
        else:
            self.timeout = timeout

    @property
    def fullname(self):
        if self._fullname is None:
            # Advisory locks are server-wide. Attempt to construct a relatively "safe" full name.
            if self._prefix is None:
                named_prefix = getattr(settings, 'ADVISORY_LOCK_NAME_PREFIX', None)
                if getattr(settings, 'ADVISORY_LOCK_PREFIX_DB_NAME', True):
                    db_name = connections.databases[self.using]['NAME']
                else:
                    db_name = None
                self._prefix = ':'.join(part for part in (named_prefix, db_name)
                                        if part is not None)
            return ':'.join(part for part in (self._prefix, self.nickname) if part)
        else:
            return self._fullname

    @fullname.setter
    def fullname(self, name):
        if name is None:
            if self.nickname is None:
                raise TypeError("inappropriate fullname, {!r}".format(name))
        else:
            self.nickname = None
        self._fullname = name

    def __call__(self, func):
        @functools.wraps(func)
        def wrapped(*args, **kws):
            with self:
                return func(*args, **kws)
        return wrapped

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def _get_cursor(self):
        connection = connections[self.using]
        return connection.cursor()

    def _execute(self, command, *args):
        cursor = self._get_cursor()
        cursor.execute(command, args)
        (result,) = cursor.fetchone()
        return result

    def acquire(self):
        result = self._execute("SELECT GET_LOCK(%s, %s)", self.fullname, self.timeout)
        if result is None:
            raise self.AcquisitionFailure("Lock acquisition failed due to a database error")
        if result == 0:
            raise self.TimeoutError("Lock acquisition timed out ({} seconds)"
                                    .format(self.timeout))
        if result != 1:
            raise self.AcquisitionFailure("Lock acquisition received unexpected result: "
                                          "{!r}".format(result))

    def release(self):
        result = self._execute("SELECT RELEASE_LOCK(%s)", self.fullname)
        if result == 0:
            raise self.ReleaseFailure("Lock {} was not established by this thread"
                                      .format(self.fullname))
        return bool(result)

    def is_free(self):
        result = self._execute("SELECT IS_FREE_LOCK(%s)", self.fullname)
        if result is None:
            raise self.LockError("Lock status check failed due to a database error")
        return bool(result)

    def user(self):
        return self._execute("SELECT IS_USED_LOCK(%s)", self.fullname)

    # TODO: warn if GET_LOCK while another one not yet released? any easy way to detect in
    # python? or need store thread-local (assuming forced release is by
    # connection)?

AdvisoryLock.LockError = LockError

AdvisoryLock.AcquisitionFailure = AcquisitionFailure
AdvisoryLock.TimeoutError = TimeoutError

AdvisoryLock.ReleaseFailure = ReleaseFailure
