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
