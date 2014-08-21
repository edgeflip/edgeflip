from functools import wraps


def retryable(exceptions_to_check, tries=4):

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
