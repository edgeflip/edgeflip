import enum

import django.core.exceptions
import django.db.models

from core.utils.descriptors import cachedclassproperty

from targetshare.utils import classonlymethod


try:
    basestring
except NameError:
    # In Python 2, basestring is the ancestor of both str and unicode;
    # in Python 3, it's just str, but was missing in 3.1
    # (Hence in Python 2, we'll support comparisons with str & unicode;
    # in Python 3, it's all "unicode" and we'll ignore the new bytes type.)
    basestring = str

try:
    unicode
except NameError:
    # In Python 3, unicode no longer exists; (it's just str)
    unicode = str


class classonlyproperty(object):
    """Descriptor decorator implementing a class-level property only accessible
    from the class.

    Attempted access to the property from the instance raises AttributeError.

    """
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        if instance is not None:
            raise AttributeError("method available to class, not instances of {}".format(owner))

        return self.func(owner)


class OrderedStrEnum(unicode, enum.Enum):
    """Ordered Enum supporting rich comparison with built-in strings.

    OrderedStrEnum are defined like a standard Enum:

        class SpinOrderedQuarks(OrderedStrEnum):

            UP = 'u'
            DOWN = 'd'
            CHARM = 'c'
            STRANGE = 's'
            TOP = 't'
            BOTTOM = 'b'

            __order__ = 'DOWN CHARM STRANGE TOP BOTTOM UP' # py2 only (see `enum`)

    Like a standard Enum, each member, defined on the class, becomes a
    singleton instance of that class. Additionally, the OrderedStrEnum extends
    the built-in string, such that its members are comparable to these:

        SpinOrderedQuarks.UP == 'u'

    Finally, taking advantage of members' definition ordering, the comparisons
    >, <, >= and <= are available as well:

        SpinOrderedQuarks.UP > 'd'

    Note that, due to the limitations of Python 2.x, only under these versions
    `__order__` is required; (and, operability with versions older than 2.7 is
    not ensured).

    """
    @cachedclassproperty
    def _member_ordinals(cls):
        return {member: index for (index, member) in enumerate(cls)}

    @classonlyproperty
    def __member_ordinals__(cls):
        """Mapping of members to their ordinals.

        Note that this is a copy of the internal mapping. It does not include
        look-up aliases.

        """
        return cls._member_ordinals.copy()

    @classonlymethod
    def get_ordinal(cls, other):
        """Retrieve the integer representing the value's place in the ordered
        enumeration and how it will compare to other enumeration values.

        Accepts both enum instances and their associated string values.

        """
        if not isinstance(other, basestring):
            raise TypeError("cannot compare object of type {!r}"
                            .format(other.__class__.__name__))

        try:
            return cls._member_ordinals[other]
        except KeyError:
            raise ValueError(other)

    @classonlymethod
    def get_member(cls, ordinal):
        """Retrieve the enum member at the given integer position."""
        name = cls._member_names_[ordinal]
        return cls[name]

    @property
    def ordinal(self):
        """The ordered enumeration member's ordinal value."""
        return self._member_ordinals[self]

    @property
    def next(self):
        """The enum member following this one.

        Returns None if this member is last in the order.

        """
        try:
            return self.__class__.get_member(self.ordinal + 1)
        except IndexError:
            return None

    @property
    def previous(self):
        """The enum member preceding this one.

        Returns None if this member is first in the order.

        """
        ordinal = self.ordinal
        if ordinal == 0:
            return None
        return self.__class__.get_member(ordinal - 1)

    def __ge__(self, other):
        return self.ordinal >= self.__class__.get_ordinal(other)

    def __gt__(self, other):
        return self.ordinal > self.__class__.get_ordinal(other)

    def __le__(self, other):
        return self.ordinal <= self.__class__.get_ordinal(other)

    def __lt__(self, other):
        return self.ordinal < self.__class__.get_ordinal(other)


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

    Also defines the class method `modelfield`, which constructs a `StatusField`
    for this Enum:

        status = Status.modelfield(default=Status.DRAFT)

    """
    @cachedclassproperty
    def choices(cls):
        """The Django model CharField `choices` listing for this enumeration."""
        if cls is AbstractStatus:
            raise NotImplementedError(
                "property 'choices' intended for concrete subclasses, not AbstractStatus")

        return tuple((member.value, member.title()) for member in cls)

    @classonlymethod
    def modelfield(cls, *args, **kws):
        return StatusField(cls, *args, **kws)

    # Members mix in unicode; necessary only to overwrite the enum default:
    def __str__(self):
        return self.value


class StatusField(django.db.models.CharField):
    """Django ORM CharField intended for use with a concrete descendent of
    AbstractStatus.

    Ensures that:

        * while statuses are strings and stored as such in the database, in the
        model field they are always represented by the appropriate Enum member
        * field instantiation arguments `choices` and `max_length` are given
        defaults appropriate to the Enum
        * South migrations are unaffected, and made to see only a CharField
        (with a built-in str default, if any)

    """
    __metaclass__ = django.db.models.SubfieldBase

    def __init__(self, statusenum, *args, **kwargs):
        # Autofill "choices":
        if 'choices' not in kwargs:
            kwargs['choices'] = statusenum.choices

        # Autofill "max_length":
        if 'max_length' not in kwargs:
            kwargs['max_length'] = max(len(value) for value in statusenum)

        super(StatusField, self).__init__(*args, **kwargs)

        self.statusenum = statusenum

    def to_python(self, value):
        # Force enum instance for consistency and error-catching
        if isinstance(value, self.statusenum) or value is None:
            return value

        try:
            return self.statusenum(value)
        except ValueError as exc:
            raise django.core.exceptions.ValidationError(exc)

    def south_field_triple(self):
        # Make South think this is just a CharField -- this field only
        # customizes Python; (and, migrations can handle themselves).
        from south.modelsinspector import introspector

        (args, kws) = introspector(self)
        if isinstance(self.default, self.statusenum):
            kws['default'] = repr(self.default.value)

        return ('django.db.models.fields.CharField', args, kws)
