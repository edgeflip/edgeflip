from __future__ import absolute_import

from functools import wraps


def retryable(on, tries=4):
    exceptions_to_check = tuple(on)

    def decorator(func):
        @wraps(func)
        def func_retry(*args, **kwargs):
            current_tries = tries
            while current_tries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions_to_check:
                    current_tries -= 1
            return func(*args, **kwargs)

        return func_retry

    return decorator
