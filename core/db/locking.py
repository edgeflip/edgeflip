import functools

from django.db import connections, DatabaseError, DEFAULT_DB_ALIAS


def lock(*args, **kws):
    if args and callable(args[0]):
        # Use as bare decorator: @lock
        # -- (but for debugging/etc. we'll pass along remaining args)
        return AdvisoryLock(*args[1:], **kws)(args[0])

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

    def __init__(self, codename=None, fullname=None, using=None, timeout=None):
        if (codename is None and fullname is None) or (codename is not None and fullname is not None):
            raise TypeError("either codename or fullname required")
        self.codename = codename
        self._fullname = fullname
        self.using = using
        # TODO: timeout required?
        self.timeout = timeout

    @property
    def fullname(self):
        if self._fullname is None:
            # TODO: return ...
            raise NotImplementedError
        return self._fullname

    @fullname.setter
    def fullname(self, name):
        if name is None:
            if self.codename is None:
                raise TypeError("inappropriate fullname: {!r}".format(name))
        else:
            self.codename = None
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

    def get_cursor(self):
        name = DEFAULT_DB_ALIAS if self.using is None else self.using
        connection = connections[name]
        return connection.cursor()

    def acquire(self):
        cursor = self.get_cursor()
        cursor.execute("SELECT GET_LOCK(%s, %s)", (self.fullname, self.timeout)) # TODO: test quoting
        (result,) = cursor.fetchone()
        # TODO: test types
        if result is None:
            raise self.AcquisitionFailure("Lock acquisition failed due to a database error")
        if result == 0:
            raise self.TimeoutError("Lock acquisition timed out ({} seconds)"
                                    .format(self.timeout))
        if result != 1:
            raise self.AcquisitionFailure("Lock acquisition received unexpected result: "
                                          "{!r}".format(result))

    def release(self):
        cursor = self.get_cursor()
        cursor.execute("SELECT RELEASE_LOCK(%s)", (self.fullname,))
        (result,) = cursor.fetchone()
        # TODO: test types
        if result == 0:
            raise self.ReleaseFailure("Lock {} was not established by this thread"
                                      .format(self.fullname))
        return bool(result)

    def is_free(self):
        raise NotImplemented

    def user(self):
        raise NotImplemented

    # TODO: warn if GET_LOCK while another one not yet released? any easy way to detect in
    # python? or need store thread-local (assuming forced release is by
    # connection)?

AdvisoryLock.LockError = LockError

AdvisoryLock.AcquisitionFailure = AcquisitionFailure
AdvisoryLock.TimeoutError = TimeoutError

AdvisoryLock.ReleaseFailure = ReleaseFailure
