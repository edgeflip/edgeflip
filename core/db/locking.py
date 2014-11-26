import functools
import inspect

from django.conf import settings
from django.db import connections, DatabaseError, DEFAULT_DB_ALIAS


def lock(*args, **kws):
    """Convenience alias for AdvisoryLock and lock nicknaming helper.

    `lock` may be invoked as a friendly alias for AdvisoryLock or as a bare
    decorator.

    When decorating a function, an appropriate nickname is generated from the
    function's module path and name. The below examples are equivalent:

        @lock
        def races(arg0, arg1):
            ...

        @lock('my.module.path:races')
        def races(arg0, arg1):
            ...

        races = lock(races)

    In the second and third examples, additional configuration arguments may be
    specified:

        @lock('my.module.path:races', using='db0')
        def races(arg0, arg1):
            ...

        races = lock(races, using='db0')

    Note that, as a bare decorator, `lock` cannot differentiate functions
    defined at the module-level from those defined in some inner context. The
    generated nickname will *only* reflect the module path and the function
    name; as such, the nickname may not reflect the decorated function's full
    import signature, (assuming it has one). This may not be a problem for your
    application. To help with the common case of decorating a class or object
    method, see `lock.method` (a.k.a. `lockingmethod`).

    """
    if args and callable(args[0]):
        # Use as decorator: @lock
        # -- (but for debugging/etc. we'll pass along remaining args)
        decorated = args[0]
        if len(args) == 1 and 'nickname' not in kws and 'fullname' not in kws:
            # No name specified, use callable's
            kws['nickname'] = "{0.__module__}:{0.__name__}".format(decorated)
        return AdvisoryLock(*args[1:], **kws)(decorated)

    # Args configure decorator / context manager object
    return AdvisoryLock(*args, **kws)


def lockingmethod(*args, **kws):
    """Factory for appropriately-nicknamed AdvisoryLock method decorators.

    Unlike `lock`, `lockingmethod` constructs its AdvisoryLock lazily, and
    assumes the decorated function will be invoked as a class or instance
    method. As such, its automatically-generated nicknames may more accurately
    reflect the function's signature.

    The below decorations are equivalent, such that both methods `races` and
    `races0` will lock with the same name, which includes the name of the class
    to which they are bound.

        class Objectified(object):

            @lockingmethod
            def races(self, arg0):
                ...

            @lock('my.module.path:Objectified.races')
            def races0(self, arg0):
                ...

    An alias for the `lockingmethod` decorator exists on the `lock` function:
    `lock.method`.

    """
    def decorator(func):
        @functools.wraps(func)
        def lazylock(obj, *innerargs, **innerkws):
            try:
                func_lock = func.lock
            except AttributeError:
                if not args and 'nickname' not in kws and 'fullname' not in kws:
                    # No name specified, use method's path
                    cls = obj if inspect.isclass(obj) else type(obj) # classmethod
                    kws['nickname'] = ("{cls.__module__}:{cls.__name__}.{func.__name__}"
                                       .format(cls=cls, func=func))
                func_lock = func.lock = AdvisoryLock(*args, **kws)

            with func_lock:
                return func(obj, *innerargs, **innerkws)

        return lazylock

    if args and callable(args[0]):
        # Use as decorator: @lockingmethod
        (decorated, args) = (args[0], args[1:])
        return decorator(decorated)
    return decorator

lock.method = lockingmethod


class LockError(DatabaseError):
    pass


class AcquisitionFailure(LockError):
    pass


class TimeoutError(AcquisitionFailure):
    pass


class ReleaseFailure(LockError):
    pass


class AdvisoryLock(object):
    """Combined context manager and decorator for reliable, high-level acquisition
    and release of advisory database locks.

    Through instantiation of an AdvisoryLock, one may configure an advisory
    database lock's name, database connection, and timeout. Used as a function
    decorator or as a context manager, the resulting object ensures acquisition
    and release of the lock, regardless of uncaught exceptions raised in the
    interlude.

    The below examples are equivalent:

        @AdvisoryLock('lock0')
        def races(arg0):
            ...

        def races(arg0):
            with AdvisoryLock('lock0'):
                ...

    For convenience, either a "nickname" or the "fullname" of the advisory lock
    may be specified. When a nickname is specified, (as in the above examples),
    the full lock name sent to the database will be prefixed, to help avoid
    naming collisions:

        * According to the `ADVISORY_LOCK_PREFIX_DB_NAME` boolean setting, (and
          by default), the full names of locks specifying only a nickname will
          be prefixed by the database name of the configured connection
          (`using`).

        * Optionally specify the setting `ADVISORY_LOCK_NAME_PREFIX` to add to
          the prefix of all of your project's nicknamed locks a custom
          ("application") name.

    Alternatively, specify `fullname` to override prefixing:

        with AdvisoryLock(fullname='blog.lock0'):
            ...

    In the above example, the full lock name sent to the database will be
    exactly "blog.lock0".

    Use of AdvisoryLock objects outside of managed contexts and decorated
    functions is not, generally, recommended; however, lower-level locking
    methods are also supplied: `acquire` and `release`.

    And, the lock object is made available to managed contexts:

        with AdvisoryLock('lock0') as lock:
            me = lock.user()
            ...

    In the above example, the method `user`, is invoked, to query the database
    for the identifier of the connection currently in control of the lock,
    (which is, of course, the current connection). AdvisoryLock also defines
    the method `is_free`, which queries the database whether the lock is
    available for acquisition.

    """
    DEFAULT_TIMEOUT = 3

    def __init__(self, nickname=None, fullname=None, using=None, timeout=None):
        if nickname is None and fullname is None:
            raise TypeError("either nickname or fullname required")
        elif nickname is not None and fullname is not None:
            raise TypeError("nickname and fullname may not both be specified")

        self.nickname = nickname

        # fullname handled dynamically
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
                # This configuration shouldn't really change, so cache it:
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
        """Request the advisory lock from the database."""
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
        """Release the advisory database lock."""
        result = self._execute("SELECT RELEASE_LOCK(%s)", self.fullname)
        if result == 0:
            raise self.ReleaseFailure("Lock {} was not established by this thread"
                                      .format(self.fullname))
        return bool(result)

    def is_free(self):
        """Query the database whether the advisory lock is available for
        acquisition.

        """
        result = self._execute("SELECT IS_FREE_LOCK(%s)", self.fullname)
        if result is None:
            raise self.LockError("Lock status check failed due to a database error")
        return bool(result)

    def user(self):
        """Request the identifier of the connection currently in control of the
        advisory database lock (if any).

        """
        return self._execute("SELECT IS_USED_LOCK(%s)", self.fullname)

    # TODO: warn if GET_LOCK while another one not yet released? any easy way to detect in
    # python? or need store thread-local (assuming forced release is by
    # connection)?

AdvisoryLock.LockError = LockError

AdvisoryLock.AcquisitionFailure = AcquisitionFailure
AdvisoryLock.TimeoutError = TimeoutError

AdvisoryLock.ReleaseFailure = ReleaseFailure
