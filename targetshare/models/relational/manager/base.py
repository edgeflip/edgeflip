import sys

from django.db import IntegrityError, models, transaction
from django.db.models.query import QuerySet
from django.utils import six


## Repeatable read ##

class RepeatableReadQuerySet(QuerySet):
    """QuerySet refined for use with the REPEATABLE READ isolation level."""

    # Copy of Django's get_or_create except %% #
    def get_or_create(self, **kwargs):
        """Looks up an object with the given kwargs, creating one if necessary.

        Returns a tuple of (object, created), where created is a boolean
        specifying whether an object was created.

        Unlike the default method, when called under Django's autocommit mode and
        the create fails, the implicit REPEATABLE READ transaction is committed, so
        as to give the final get of a race condition's losing thread a chance at
        retrieving the winning thread's object. Note that the behavior of this method
        under transaction management is unchanged, and its use and/or implementation
        should be considered for this case.

        """
        assert kwargs, \
                'get_or_create() must be passed at least one keyword argument'
        defaults = kwargs.pop('defaults', {})
        lookup = kwargs.copy()
        for f in self.model._meta.fields:
            if f.attname in lookup:
                lookup[f.name] = lookup.pop(f.attname)
        try:
            self._for_write = True
            return self.get(**lookup), False
        except self.model.DoesNotExist:
            try:
                params = dict([(k, v) for k, v in kwargs.items() if '__' not in k])
                params.update(defaults)
                obj = self.model(**params)
                sid = transaction.savepoint(using=self.db)
                obj.save(force_insert=True, using=self.db)
                transaction.savepoint_commit(sid, using=self.db)
                return obj, True
            except IntegrityError:
                transaction.savepoint_rollback(sid, using=self.db)

                # %% Commit implicit REPEATABLE READ transaction:
                transaction.commit_unless_managed()

                exc_info = sys.exc_info()
                try:
                    return self.get(**lookup), False
                except self.model.DoesNotExist:
                    # Re-raise the IntegrityError with its original traceback.
                    six.reraise(*exc_info)


class Manager(models.Manager):

    def get_query_set(self):
        return RepeatableReadQuerySet(self.model, using=self._db)


## Configurable RelatedManagers ##

class ConfigurableManager(models.Manager):
    """Manager base class supporting configuration of its instances and QuerySets,
    upon instantiation, without modification of its inherited instantiation signature
    (no arguments), thereby retaining its use as a RelatedManager.

        class MyManager(ConfigurableManager):

            @classmethod
            def configure(cls, instance, my_arg1, my_arg2=None):
                instance.my_arg1 = my_arg1
                instance.my_arg2 = my_arg2

            # Manager methods, QuerySet proxy methods, etc.

        class MyModel(Model):

            objects = MyManager.make('foo')

    By defining a `configure` class method, rather than extending __init__, and
    instantiating via the manager class's `make` method, a manager configured to the
    model's needs is constructed on-the-fly, and which supports subclassing by Django's
    RelatedManager without loss of configuration.

    Furthermore, this configuration may be extended to QuerySets trivially --

        class MyQuerySet(ConfigurableQuerySet):

            def method_requiring_configuration(self):
                ...

        class MyManager(ConfigurableManager):

            queryset = MyQuerySet

            @classmethod
            def configure(cls, instance, my_arg1, my_arg2=None):
                instance.my_arg1 = my_arg1
                instance.my_arg2 = my_arg2

    The `configure` method will be applied to instances of the manager's `queryset`
    as well.

    """
    queryset = RepeatableReadQuerySet

    @classmethod
    def configure(cls, instance, *args, **kws):
        raise NotImplementedError

    @classmethod
    def make(cls, *args, **kws):
        """Manufacture a concrete, configured Manager, and return an instance of
        this class.

        """
        class ConfiguredManager(cls):

            def __init__(self):
                super(ConfiguredManager, self).__init__()

                def configurer(instance):
                    return cls.configure(instance, *args, **kws)
                configurer.func = cls.configure
                configurer.args = args
                configurer.kws = kws
                self.configurer = configurer

                self.configurer(self)

        return ConfiguredManager()

    def get_query_set(self):
        try:
            make = self.queryset.make
        except AttributeError:
            return self.queryset(self.model, using=self._db)
        else:
            return make(self)


class ConfigurableQuerySet(RepeatableReadQuerySet):

    @classmethod
    def make(cls, manager):
        instance = cls(manager.model, using=manager._db)
        instance.manager = manager
        instance.configure()
        return instance

    def _clone(self, klass=None, setup=False, **kwargs):
        kwargs.update(manager=self.manager)
        clone = super(ConfigurableQuerySet, self)._clone(klass, setup, **kwargs)
        clone.configure()
        return clone

    def configure(self):
        self.manager.configurer(self)
