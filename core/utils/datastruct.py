"""Data modeling library producing memory-light objects."""
import abc
import collections

from core.utils.descriptors import cachedclassproperty


NOTSET = object()


class Field(object):
    """Model fields are declared in model class definitions, via instances of
    subclasses of Field.

    Fields then control the input and output of object data, mainly by
    "cleaning" input data -- validating and regularizing it.

    """
    __metaclass__ = abc.ABCMeta

    # SlotFields.__new__ sets reference to slot member_descriptor,
    # which controls low-level data management.

    def __init__(self, default=NOTSET):
        self.default = default
        self.member = None

    def __get__(self, instance, owner, use_default=True):
        if instance is None:
            return self

        try:
            return self.member.__get__(instance, owner)
        except AttributeError:
            if self.default is NOTSET or not use_default:
                raise
            return self.default

    def __set__(self, instance, value):
        clean = self.clean(instance, value)
        self.member.__set__(instance, clean)

    # Subclasses of Field define their method of validating and regularizing
    # data set on the instance:
    @abc.abstractmethod
    def clean(self, instance, value):
        raise NotImplementedError


class InternalField(Field):

    def clean(self, instance, value):
        return value


class IntegerField(Field):

    def clean(self, instance, value):
        return int(value)


class FloatField(Field):

    def clean(self, instance, value):
        return float(value)


class CharField(Field):

    def clean(self, instance, value):
        if isinstance(value, unicode):
            return value
        elif isinstance(value, str):
            return value.decode('utf8')
        else:
            return unicode(value)


class ReferenceField(Field):

    def __init__(self, cls, *args, **kws):
        super(ReferenceField, self).__init__(*args, **kws)
        self.reference = cls

    def clean(self, instance, value):
        if isinstance(value, self.reference):
            return value

        refname = getattr(self.reference, '__name__', self.reference)
        raise TypeError("{} expected value of type '{}', got '{}'"
                        .format(self.__class__.__name__, refname, value.__class__.__name__))


class SlotFields(abc.ABCMeta):
    """Metaclass which collects Field instances from the class definition
    namespace, allows `type` to set slots' `member_descriptors`, and ties these
    to the declared Fields.

    Extends ABCMeta for support of (optional) abstract classes.

    """
    @classmethod
    def __prepare__(mcs, name, bases):
        # In Py3k, this makes fields (and __slots__) ordered, and thereby
        # enables reliable instantiation by anonymous arguments.
        return collections.OrderedDict()

    def __new__(mcs, name, bases, namespace):
        # Collect fields from class declaration:
        fields = collections.OrderedDict()
        for (field_name, obj) in namespace.items():
            if isinstance(obj, Field):
                fields[field_name] = namespace.pop(field_name)

        # Set __slots__ to initiate Python's default handling:
        namespace['__slots__'] = fields.keys()
        cls = super(mcs, SlotFields).__new__(mcs, name, bases, namespace)

        # Re-set fields, now with reference to newly-created slot desciptors:
        for (field_name, field) in fields.items():
            field.member = getattr(cls, field_name)
            setattr(cls, field_name, field)

        return cls


class DataStruct(object):
    """Data-modeling base class, supporting declarative, type-aware field
    definition, and automatic definition of __slots__ (for improved memory
    management).

    Example:

        class User(DataStruct):

            uid = IntegerField()
            first_name = CharField()
            last_name = CharField()

        user = User(uid='123', first_name='Joe', last_name=1)
        user.uid == 123
        user.last_name == u'1'

        User.__slots__ == ['uid', 'first_name', 'last_name'] # Sorted in Py3k only

    """
    __metaclass__ = SlotFields

    @classmethod
    def __iterslots__(cls):
        seen = set()
        for kls in reversed(cls.mro()):
            for slot in getattr(kls, '__slots__', ()):
                if slot in seen:
                    continue
                seen.add(slot)
                yield slot

    @cachedclassproperty
    def _allslots(cls):
        return tuple(cls.__iterslots__())

    @cachedclassproperty
    def _publicslots(cls):
        return tuple(slot for slot in cls._allslots
                     if not isinstance(getattr(cls, slot), InternalField))

    def __init__(self, *args, **kws):
        if len(args) > len(self._publicslots):
            raise TypeError("{} expected at most {} arguments, got {}"
                            .format(self.__class__.__name__, len(self._publicslots), len(args)))

        for (name, value) in zip(self._publicslots, args):
            setattr(self, name, value)

        remainder = self._publicslots[len(args):]
        for (name, value) in kws.iteritems():
            if name in self._publicslots:
                if name in remainder:
                    setattr(self, name, value)
                else:
                    raise TypeError("{} got multiple values for keyword argument '{}'"
                                    .format(self.__class__.__name__, name))
            else:
                raise TypeError("{} got an unexpected keyword argument '{}'"
                                .format(self.__class__.__name__, name))

    @property
    def __dict__(self):
        variables = collections.OrderedDict()

        # Access descriptors directly to avoid "defaults" (which are not stored data).
        cls = type(self) # for easy access to descriptors
        for name in cls._allslots:
            field = getattr(cls, name)
            try:
                variables[name] = field.__get__(self, cls, use_default=False)
            except AttributeError:
                pass

        return variables

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        for (name, value) in state.iteritems():
            setattr(self, name, value)

    def clone(self, **replace):
        data = dict(self.__dict__, **replace) if replace else self.__dict__
        return type(self)(**data)

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ', '.join("{}={!r}".format(*item) for item in self.__dict__.items())
        )
