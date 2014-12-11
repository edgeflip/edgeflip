import enum

from django.utils.functional import cached_property


class OrderedStrEnum(str, enum.Enum):
    """Ordered Enum supporting rich comparison with instances of basestring.

    OrderedStrEnum are defined like a standard Enum:

        class SpinOrderedQuarks(OrderedStrEnum):

            UP = 'u'
            DOWN = 'd'
            CHARM = 'c'
            STRANGE = 's'
            TOP = 't'
            BOTTOM = 'b'

            __order__ = 'DOWN CHARM STRANGE TOP BOTTOM UP' # py2 only

    Like a standard Enum, each element, defined on the class, becomes a
    singleton instance of that class. Additionally, the OrderedStrEnum extends
    str, such that its elements are comparable to strs:

        SpinOrderedQuarks.UP == 'u'

    Taking advantage of the elements' ordering, the comparisons >,<,>=,<= are
    available as well:

        SpinOrderedQuarks.UP > 'd'

    Note that, due to the limitations of Python 2.x, only under these versions
    `__order__` is required; (and, operability with versions older than 2.7 is
    not ensured).

    """
    @classmethod
    def _ordinal(cls, other):
        for (index, value) in enumerate(cls._member_map_.itervalues()):
            if value == other:
                return index

    @classmethod
    def _get_ordinal(cls, other):
        if not isinstance(other, basestring):
            raise TypeError("cannot compare object of type {!r}"
                            .format(other.__class__.__name__))

        ordinal = cls._ordinal(other)
        if ordinal is None:
            raise ValueError(other)

        return ordinal

    @cached_property
    def ordinal(self):
        return self._ordinal(self)

    def __ge__(self, other):
        return self.ordinal >= self._get_ordinal(other)

    def __gt__(self, other):
        return self.ordinal > self._get_ordinal(other)

    def __le__(self, other):
        return self.ordinal <= self._get_ordinal(other)

    def __lt__(self, other):
        return self.ordinal < self._get_ordinal(other)


class cached_class_property(object):
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
            return getattr(cls, self.cache_name)
        except AttributeError:
            result = self.func(cls)
            setattr(cls, self.cache_name, result)
            return result


class AbstractStatus(OrderedStrEnum):
    """OrderedStrEnum intended for Django models whose status fields represent
    directed graphs.

    Defines the caching property `choices`, corresponding to the CharField
    parameter "choices", and defines `__str__` to support the field paramter
    "default":

        class Status(AbstractStatus):

            DRAFT = 'draft'
            PUBLISHED = 'published'
            ARCHIVED = 'archived'

        status = CharField(max_length=10,
                           default=Status.DRAFT,
                           choices=Status.choices)

    """
    @cached_class_property
    def choices(cls):
        if cls is AbstractStatus:
            raise NotImplementedError(
                "property 'choices' intended for concrete subclasses, not AbstractStatus")

        return tuple(
            (str(value), value.title())
            for value in cls._member_map_.itervalues()
        )

    def __str__(self):
        return self.value
