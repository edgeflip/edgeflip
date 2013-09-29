import operator
import sys
from collections import defaultdict

from django.db import IntegrityError, models, transaction
from django.db.models.query import QuerySet
from django.utils import six, timezone

from targetshare import utils


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


class TransitoryObjectQuerySet(RepeatableReadQuerySet):

    def for_datetime(self, datetime=None):
        datetime = datetime or timezone.now()
        return self.filter(
            models.Q(end_dt=None) | models.Q(end_dt__lt=datetime),
            start_dt__lte=datetime,
        )


class TransitoryObjectManager(models.Manager):

    def get_query_set(self):
        return TransitoryObjectQuerySet(self.model, using=self._db)

    def for_datetime(self, datetime=None):
        return self.get_query_set().for_datetime(datetime)


class AssignedObjectQuerySet(RepeatableReadQuerySet):

    # Field of related object to assign:
    assigned_object = None
    rand_cdf = 'rand_cdf'

    def __init__(self, model=None, query=None, using=None, assigned_object=None):
        super(AssignedObjectQuerySet, self).__init__(model, query, using)
        self.assigned_object = assigned_object

    def _clone(self, klass=None, setup=False, **kwargs):
        clone = super(AssignedObjectQuerySet, self)._clone(klass, setup, **kwargs)
        if hasattr(clone, 'assigned_object'):
            clone.assigned_object = self.assigned_object
        return clone

    def random_assign(self):
        if not self.assigned_object:
            raise TypeError("Assigned object field not set")

        for field in self.model._meta.fields:
            if field.name == self.assigned_object:
                assigned_class = field.related.parent_model
                break
        else:
            raise TypeError("Field {!r} not found on model {meta.app_label}.{meta.object_name}"
                            .format(self.assigned_object, meta=self.model._meta))

        options = self.values_list(self.assigned_object, self.rand_cdf)
        object_id = utils.random_assign(options)
        return assigned_class.objects.get(pk=object_id)


class AssignedTransitoryObjectQuerySet(AssignedObjectQuerySet, TransitoryObjectQuerySet):
    pass


class AssignedObjectManager(TransitoryObjectManager):

    assigned_object = None

    def get_query_set(self):
        return AssignedTransitoryObjectQuerySet(self.model,
            using=self._db, assigned_object=self.assigned_object)

    def random_assign(self):
        return self.get_query_set().random_assign()


class AssignedFilterManager(AssignedObjectManager):

    assigned_object = 'filter'


class AssignedChoiceSetManager(AssignedObjectManager):

    assigned_object = 'choice_set'


class AssignedButtonStyleManager(AssignedObjectManager):

    assigned_object = 'button_style'


class AssignedFacesStyleManager(AssignedObjectManager):

    assigned_object = 'faces_style'


class AssignedFBObjectManager(AssignedObjectManager):

    assigned_object = 'fb_object'


class StartStopManager(models.Manager):
    """Model manager supporting related objects which must be expired and replaced by
    fresh objects, rather than updated or deleted.

    It is assumed that models making use of this manager have a "start" DateTimeField
    and, more importantly, an "end" DateTimeField; the "end" field, when set, indicates
    that the object is no longer active.

    See method `replace`.

    """
    # Factory method needed to preserve argument-less __init__ for RelatedManager.
    # Also see start_stop_manager():
    @classmethod
    def make(cls, *signature, **kws):
        """Manufacture a StartStopManager to manage model objects with the given
        `signature` and return an instance of this class.

        """
        end_field = kws.pop('end_field', 'end_dt')
        if kws:
            raise TypeError("Invalid keyword arguments for make: {}"
                            .format(', '.join(kws)))

        class ConcreteStartStopManager(cls):

            def __init__(self):
                super(ConcreteStartStopManager, self).__init__()
                self.signature = signature
                self.end_field = end_field

        return ConcreteStartStopManager()

    def __init__(self):
        super(StartStopManager, self).__init__()
        self.signature = None
        self.end_field = None

    def _map_object_data(self, obj):
        """Reduce a model object or a dict to a stream of key-value pairs."""
        if isinstance(obj, self.model):
            # Break the model object down. Don't bother with __dict__ to
            # preserve nice descriptor interface:
            for field in self.model._meta.fields:
                if field.rel:
                    try:
                        value = getattr(obj, field.name)
                    except field.rel.to.DoesNotExist:
                        value = None
                else:
                    value = getattr(obj, field.name)
                yield field.name, value
        else:
            # Break down dict:
            try:
                iterable = obj.items()
            except AttributeError:
                iterable = obj

            for item in iterable:
                yield item

    def replace(self, data, replace_all=False):
        """Replace the RelatedManager's active objects with new objects as specified by
        an iterable of new associated object data.

        Objects are considered "active" whose DateTimeField, which we'll call its
        "end_field", is NULL; (by default, the name of this field is assumed to be
        "end_dt").

        By default, pre-existing, active objects whose signatures conflict with the
        objects to be inserted are expired by setting "end_field" to the current
        datetime. Pass the `replace_all` flag to expire all associated objects.

        For example::

            class Filter(models.Model):
                ...

            class FilterFeature(models.Model):
                filter = models.ForeignKey(Filter)
                feature = models.CharField()
                operator = models.CharField()
                start_dt = models.DateTimeField(auto_now_add=True)
                end_dt = models.DateTimeField(null=True)

                objects = start_stop_manager('feature', 'operator')

            my_filter = Filter.objects.get(pk=1)
            my_filter.filterfeature_set.replace([
                {'feature': 'foo', operator: 'min'},
                {'feature': 'foo', operator: 'max'},
                {'feature': 'bar', operator: 'min'},
            ])

        As called above, `replace`:

            1) validates that unique `FilterFeature`s will be inserted, where
                the object signature has been passed to the manager through the factory
                function `start_stop_manager`
            2) expires the currently active set of `FilterFeature`s whose
                signatures match those to be inserted, by setting `end_dt`
            3) inserts the new `FilterFeature`s under `Filter` `my_filter`

        Alternatively, `replace_all` may be specified, such that all active
        `FilterFeature`s are expired and replaced by the new data. And, regardless,
        data may also be specified as model objects::

            my_filter.filterfeature_set.replace(
                [
                    FilterFeature(feature='foo', operator='min'),
                    FilterFeature(feature='foo', operator='max'),
                    FilterFeature(feature='bar', operator='min'),
                ],
                replace_all=True,
            )

        """
        # Avoid accidental application to all instances of parent model:
        if not getattr(self, 'instance', None):
            raise TypeError("replace intended for use on related managers")

        # Normalize data:
        data = tuple(dict(self._map_object_data(obj)) for obj in data)

        # Check new data uniqueness:
        signatures = defaultdict(lambda: 0)
        for object_data in data:
            signatures[tuple(object_data[field] for field in self.signature)] += 1
        object_data_dupes = tuple(
            signature for signature, count in signatures.items() if count > 1
        )
        if object_data_dupes:
            raise ValueError(
                "Associated objects must be unique on columns {!r}. "
                "Duplicates found for {!r}".format(self.signature, object_data_dupes)
            )

        # Determine related objects to replace:
        if replace_all:
            replaced = self.filter(**{self.end_field: None})
        elif data:
            # Objects to replace match all columns in fields (&) for any set
            # of data (|):
            conditions = reduce(operator.or_, ( # |
                reduce(operator.and_, ( # &
                    models.Q(**{field: object_data[field]}) for field in self.signature
                )) for object_data in data
            ))
            replaced = self.filter(conditions, **{self.end_field: None})
        else:
            raise ValueError("Empty data set given and replace_all not specified. "
                             "Can neither expire old objects nor create new ones.")

        # Expire replaced objects:
        replaced.update(**{self.end_field: timezone.now()})

        # Insert and return new objects:
        return tuple(self.create(**object_data) for object_data in data)

start_stop_manager = StartStopManager.make
