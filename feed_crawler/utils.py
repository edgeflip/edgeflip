from __future__ import absolute_import

from functools import wraps


def retryable(on=None, tries=4, logger=None):
    if not on:
        return

    exceptions_to_check = tuple(on)

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries = tries
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions_to_check as e:
                    msg = "%s, Retrying..." % (str(e))
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    mtries -= 1
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
