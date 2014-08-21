from functools import wraps


def retryable(*exceptions_to_check, **kwargs):
    tries = kwargs.pop('tries', 4)
    if kwargs:
        raise TypeError

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
