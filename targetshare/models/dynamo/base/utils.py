class cached_property(object):
    """property-like descriptor, which caches its result in instance dictionary."""

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        result = vars(instance)[self.func.__name__] = self.func(instance)
        return result
