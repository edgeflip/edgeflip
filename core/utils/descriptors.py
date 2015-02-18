class cachedclassproperty(object):
    """Descriptor decorator implementing a class-level property, which caches
    its results on the classes on which it operates.

    This descriptor supports inheritance, because it never replaces itself with
    any value; rather, it stores its values under its access name with added
    underscores. For example, when wrapping getters named "choices",
    "choices_" or "_choices", each class's result is stored on the class at
    "_choices_"; decoration of a getter named "_choices_" would raise an
    exception.

    """
    def __init__(self, func):
        self.func = func
        self.cache_name = '_{}_'.format(func.__name__.strip('_'))
        if self.cache_name == func.__name__:
            raise ValueError("alias conflict: {}".format(self.cache_name))

    def __get__(self, instance, cls=None):
        if cls is None:
            cls = type(instance)

        try:
            return vars(cls)[self.cache_name]
        except KeyError:
            result = self.func(cls)
            setattr(cls, self.cache_name, result)
            return result
