import abc


class AutoRegistering(abc.ABCMeta):
    """Type which, upon class definition, invokes the the class's `__register__` method.

    The `__register__` method must be implemented at least by the base class of any family which
    instantiates this type.

    For example, the following family of classes uses the registration hook to populate a shared
    list of members:

        class Base(object):
            __metaclass__ = AutoRegistering
            _registry_ = []

            @classmethod
            def __register__(cls):
                cls._registry_.append(cls)

            @classmethod
            def __registry__(cls):
                return cls._registry_[:]

        class SubA(Base):
            pass

        assert SubA.__registry__() == [Base, SubA]

    (See also: `InternalRegistering`.)

    Note, AutoRegistering extends ABCMeta, and so classes implementing this type may also define
    abstract methods and properties.

    """
    @abc.abstractmethod
    def __register__(cls):
        raise NotImplementedError

    def __init__(cls, name, bases, namespace):
        super(AutoRegistering, cls).__init__(name, bases, namespace)
        cls.__register__()


class InternalRegistering(AutoRegistering):
    """A type which tracks subclasses of any base class in a shared list.

        class Base(object):
            __metaclass__ = InternalRegistering

        class SubA(Base):
            pass

        assert SubA.__registry__() == [Base, SubA]

    The base class may be excluded from this list with the class attribute `__registers_base__`:

        class Base(object):
            __metaclass__ = InternalRegistering
            __registers_base__ = False

    """
    def __register__(cls):
        try:
            registry = cls._registry_
        except AttributeError:
            # This must be the base class. Create registry:
            registry = cls._registry_ = []
            if not getattr(cls, '__registers_base__', True):
                return

        # Register (sub)class:
        registry.append(cls)

    def __registry__(cls):
        return cls._registry_[:]


def autoregistry(func=None, name=None, bases=(object,), mixin=None):
    """Decorator factory for the definition of a base class which tracks its child classes.

    Rather than requiring that you define a base class, which uses the AutoRegistering metaclass
    and defines its __register__ method, `autoregistry` distills this definition to the
    registration method -- for example:

        @autoregistry
        def registered_base(cls):
            registered_base.__registry__.append(cls)
        registered_base.__registry__ = []

        class A(registered_base):
            pass

        class B(registered_base):
            pass

        assert B.__registry__ == [A, B]

    In fact, the registry may be stored anywhere, and itself be any data type; (the above is merely
    a reasonable example). This example is functionally (though not internally) the same as the
    following without the decorator:

        class registered_base(object):

            __metaclass__ = AutoRegistering

            @classmethod
            def __register__(cls):
                try:
                    registry = cls.__registry__
                except AttributeError:
                    cls.__registry__ = []
                else:
                    registry.append(cls)

    The base class manufactured by the decorator may also be configured:

        @autoregistry(name='Base', bases=(AnotherBase,), mixin={'var1': 1})
        def registered_base(cls):
            ...

    """
    def decorator(func):
        def __register__(cls):
            if decorator.basecall:
                func(cls)
            else:
                decorator.basecall = True

        namespace = {} if mixin is None else mixin.copy()
        namespace.update(
            __module__=func.__module__,
            __register__=classmethod(__register__),
        )
        return AutoRegistering((name or func.__name__), bases, namespace)

    decorator.basecall = False

    if func is None:
        return decorator

    return decorator(func)
