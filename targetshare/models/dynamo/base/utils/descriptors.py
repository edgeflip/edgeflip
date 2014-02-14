class cached_property(object):
    """property-like descriptor which caches its result in the instance dictionary."""

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        result = vars(instance)[self.func.__name__] = self.func(instance)
        return result


class class_property(object):
    """property-like descriptor which passes the wrapped method the class,
    rather than the instance, and which operates identically whether accessed
    from the class or an instance.

    """
    def __init__(self, func=None):
        self.func = func

    def __get__(self, instance, cls=None):
        if cls is None:
            cls = type(instance)
        return self.func(cls)
