import re

from core.models.manager import Manager, RepeatableReadQuerySet


class TypeObjectManager(Manager):

    code_field_name = 'code'
    code_pattern = re.compile(r'^get_([a-z_]+)$')

    def __getattr__(self, attr):
        code_match = self.code_pattern.search(attr)
        if code_match:
            code_name = code_match.group(1)
            try:
                code = getattr(self.model, code_name.upper())
            except AttributeError:
                pass
            else:
                if isinstance(code, basestring):
                    def getter():
                        return self.get(**{self.code_field_name: code})
                    getter.__name__ = attr
                    setattr(self, attr, getter)
                    return getter

        raise AttributeError("'{}' object has no attribute {!r}"
                             .format(self.__class__.__name__, attr))


## Configurable RelatedManagers ##

class ConfigurableManager(Manager):
    """Manager base class supporting configuration of its instances and QuerySets,
    upon instantiation, without modification of its inherited instantiation signature
    (no arguments), thereby retaining its use as a RelatedManager.

        class MyManager(ConfigurableManager):

            def configure(self, instance, my_arg1, my_arg2=None):
                instance.my_arg1 = my_arg1
                instance.my_arg2 = my_arg2

            # Manager methods, QuerySet proxy methods, etc.

        class MyModel(Model):

            objects = MyManager.make('foo')

    By defining a `configure` method, rather than extending __init__, and by
    instantiating via the manager class's `make` method, a manager configured to the
    model's needs is constructed on-the-fly, and which supports subclassing by Django's
    RelatedManager without loss of configuration.

    Furthermore, this configuration may be extended to QuerySets trivially --

        class MyQuerySet(ConfigurableQuerySet):

            def method_requiring_configuration(self):
                ...

        class MyManager(ConfigurableManager):

            def configure(self, instance, my_arg1, my_arg2=None):
                instance.my_arg1 = my_arg1
                instance.my_arg2 = my_arg2

            def get_query_set(self):
                return MyQuerySet.make(self)

    MyManager's `configure` method will now be applied to instances of the manager's
    queryset, MyQuerySet, as well.

    """
    def configure(self, instance, *args, **kws):
        """Configure the given object with parameters specified to `make`.

        `configure` stands in for __init__, whose interface cannot otherwise be
        extended without breaking support for RelatedManagers. Additionally,
        `configure` is applied to ConfigurableQuerySets constructed via their own
        `make`.

        Made concrete by user.

        """
        raise NotImplementedError

    def configure_object(self, instance):
        """Configure the given object by passing `make` parameters to the user-
        defined `configure` method.

        Made concrete by `make`.

        """
        raise NotImplementedError

    @classmethod
    def make(cls, *args, **kws):
        """Manufacture a concrete, configured Manager, and return an instance of
        this class.

        """
        class ConfiguredManager(cls):

            def configure_object(self, instance):
                """Configure the given object by passing `make` parameters to the user-
                defined `configure` method.

                """
                return self.configure(instance, *args, **kws)

            # For debugging:
            configure_object.args = args
            configure_object.kws = kws

            def __init__(self):
                super(ConfiguredManager, self).__init__()
                self.configure_object(self)

        return ConfiguredManager()


class ConfigurableQuerySet(RepeatableReadQuerySet):

    @classmethod
    def make(cls, manager):
        instance = cls(manager.model, using=manager._db)
        instance.configure(manager)
        return instance

    def _clone(self, klass=None, setup=False, **kwargs):
        clone = super(ConfigurableQuerySet, self)._clone(klass, setup, **kwargs)
        try:
            configure = clone.configure
        except AttributeError:
            # _clone is used to create e.g. ValuesQuerySets, which we can't
            # (and needn't) configure
            pass
        else:
            configure(self.manager)
        return clone

    def configure(self, manager=None):
        if manager:
            self.manager = manager
        self.manager.configure_object(self)
