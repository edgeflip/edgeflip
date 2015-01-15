import abc

from nose import tools

from core.utils import classregistry


class TestAutoRegistering(object):

    def test_hook(self):
        class Base(object):
            __metaclass__ = classregistry.AutoRegistering
            _registry_ = []

            @classmethod
            def __register__(cls):
                cls._registry_.append(cls)

        tools.eq_(Base._registry_, [Base])

        class SubA(Base):
            pass

        tools.eq_(Base._registry_, [Base, SubA])

    @tools.raises(NotImplementedError)
    def test_hook_unimplemented(self):
        class Base(object):
            __metaclass__ = classregistry.AutoRegistering

    def test_abstract_methods(self):
        class Base(object):
            __metaclass__ = classregistry.AutoRegistering
            _registry_ = []

            @classmethod
            def __register__(cls):
                cls._registry_.append(cls)

            @abc.abstractmethod
            def abstract(self):
                pass

        class SubA(Base):
            pass

        with tools.assert_raises(TypeError):
            SubA()


class TestInternalRegistering(object):

    def test_registration(self):
        class Base(object):
            __metaclass__ = classregistry.InternalRegistering

        tools.eq_(Base._registry_, [Base])

        class SubA(Base):
            pass

        tools.eq_(Base._registry_, [Base, SubA])

    def test_ignore_base(self):
        class Base(object):
            __metaclass__ = classregistry.InternalRegistering
            __registers_base__ = False

        tools.eq_(Base._registry_, [])

        class SubA(Base):
            pass

        tools.eq_(Base._registry_, [SubA])

    def test_registry_interface(self):
        class Base(object):
            __metaclass__ = classregistry.InternalRegistering

        class SubA(Base):
            pass

        registry = Base.__registry__()
        tools.eq_(registry, [Base, SubA])
        tools.eq_(registry, Base._registry_)
        tools.eq_(SubA.__registry__(), registry)
        tools.assert_is_not(registry, Base._registry_)


class TestAutoRegistry(object):

    class MixIn(object):
        pass

    def test_defn(self):
        def register(cls):
            registry.append(cls)
        registry = []

        extra = {'VAR': 1}
        Base = classregistry.autoregistry(register, 'Base', (self.MixIn,), extra)

        tools.eq_(Base.__name__, 'Base')
        tools.eq_(Base.mro(), [Base, self.MixIn, object])
        tools.eq_(Base.VAR, 1)
        tools.eq_(extra, {'VAR': 1})
        tools.eq_(registry, [])

        class SubA(Base):
            pass

        tools.eq_(registry, [SubA])

    def test_decorator(self):
        @classregistry.autoregistry
        def register(cls):
            register.registry.append(cls)
        register.registry = []

        class SubA(register):
            pass

        tools.eq_(register.__name__, 'register')
        tools.eq_(register.registry, [SubA])
        tools.eq_(SubA.registry, [SubA])

    def test_decorator_factory(self):
        @classregistry.autoregistry(name='RegisteringBase', bases=(self.MixIn,), mixin={'VAR': 1})
        def register(cls):
            register.registry.append(cls)
        register.registry = []

        class SubA(register):
            pass

        tools.eq_(register.__name__, 'RegisteringBase')
        tools.eq_(register.registry, [SubA])
        tools.eq_(SubA.registry, [SubA])
        tools.eq_(register.mro(), [register, self.MixIn, object])
        tools.eq_(register.VAR, 1)
