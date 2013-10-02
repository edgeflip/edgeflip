import operator
from collections import defaultdict

from django.db import models
from django.utils import timezone

from . import base


def map_object_data(model, obj):
    """Reduce a model object or a dict to a stream of key-value pairs."""
    if isinstance(obj, model):
        # Break the model object down. Don't bother with __dict__ to
        # preserve nice descriptor interface:
        for field in model._meta.fields:
            if field.rel:
                try:
                    value = getattr(obj, field.name)
                except field.rel.to.DoesNotExist:
                    value = None
            else:
                value = getattr(obj, field.name)
            yield field.name, value

    elif isinstance(obj, models.Model):
        raise TypeError("Model mismatch")

    else:
        # Break down dict:
        try:
            iterable = obj.items()
        except AttributeError:
            iterable = obj

        for item in iterable:
            yield item


class TransitoryObjectQuerySet(base.ConfigurableQuerySet):

    def for_datetime(self, datetime=None):
        datetime = datetime or timezone.now()
        return self.filter(
            models.Q(end_dt=None) | models.Q(end_dt__lt=datetime),
            start_dt__lte=datetime,
        )

    def source(self, obj, default_attrs=None):
        """Conditionally store the given object, retiring any active, attribute-
        conflicting objects in the related object's set.

        Object default attributes may be specified, which are written to the given
        raw object.

        The up-to-date object is returned, (which, in case of a match, may be the
        pre-existing, rather than the specified, object).

        """
        source_fields = getattr(self, 'source_fields', None)
        if not source_fields:
            raise TypeError("method requires specification of source_fields")

        source_fields = [getattr(field, 'name', field) for field in source_fields]

        parent = getattr(self, 'instance', None)
        if not parent:
            raise TypeError("method intended for use with RelatedManagers")

        if not isinstance(obj, self.model):
            raise TypeError("Model mismatch")

        rel_fields = [field for field in self.model._meta.fields
                      if field.rel and isinstance(parent, field.rel.to)]
        try:
            (rel_field,) = rel_fields
        except ValueError:
            raise TypeError("method does not currently support multiple "
                            "relationships with a single parent")
        related_name = rel_field.name
        related_obj = getattr(obj, related_name)
        if related_obj is None:
            setattr(obj, related_name, parent)
        elif related_obj != parent:
            raise ValueError("Related object mismatch")

        # Fill in defaults:
        if default_attrs is not None:
            for field in source_fields:
                if not getattr(obj, field):
                    default_value = getattr(default_attrs, field)
                    setattr(obj, field, default_value)

        try:
            existing = self.for_datetime().get()
        except self.model.DoesNotExist:
            pass
        else:
            if all(
                getattr(obj, field) == getattr(existing, field)
                for field in source_fields
            ):
                # Update unnecessary
                return existing

        # Store new attrs:
        obj.save()
        # Retire old, at end, and expansively, to handle races:
        self.for_datetime().exclude(pk=obj.pk).update(end_dt=timezone.now())
        return obj

    def replace(self, data, replace_all=False):
        """Replace the query's active objects with new objects as specified by
        an iterable of new associated object data.

        Objects are considered "active" whose DateTimeField, which we'll call its
        "end_field", is NULL -- (by default, the name of this field is assumed to be
        "end_dt") -- or which are otherwise active for the current datetime; (see
        `for_datetime()`).

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

                objects = TransitoryObjectManager.make(signature_fields=[feature, operator])

            my_filter = Filter.objects.get(pk=1)
            my_filter.filterfeature_set.replace([
                {'feature': 'foo', operator: 'min'},
                {'feature': 'foo', operator: 'max'},
                {'feature': 'bar', operator: 'min'},
            ])

        As called above, `replace`:

            1) validates that unique `FilterFeature`s will be inserted, where
                the object signature has been passed to the manager through the factory
                method `TransitoryObjectManager.make`
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
        signature_fields = getattr(self, 'signature_fields', None)
        if not signature_fields:
            raise TypeError("method requires specification of signature_fields")

        signature_fields = [getattr(field, 'name', field) for field in signature_fields]

        # Avoid accidental application to all instances of parent model:
        if not getattr(self, 'instance', None):
            raise TypeError("method intended for use with RelatedManagers")

        # Normalize data:
        data = tuple(dict(map_object_data(self.model, obj)) for obj in data)

        # Check new data uniqueness:
        signatures = defaultdict(lambda: 0)
        for object_data in data:
            signatures[tuple(object_data[field] for field in signature_fields)] += 1
        object_data_dupes = tuple(
            signature for signature, count in signatures.items() if count > 1
        )
        if object_data_dupes:
            raise ValueError(
                "Associated objects must be unique on columns {!r}. "
                "Duplicates found for {!r}".format(signature_fields, object_data_dupes)
            )

        # Determine related objects to replace:
        if replace_all:
            replaced = self.for_datetime()
        elif data:
            # Objects to replace match all columns in fields (&) for any set
            # of data (|):
            conditions = reduce(operator.or_, ( # |
                reduce(operator.and_, ( # &
                    models.Q(**{field: object_data[field]}) for field in signature_fields
                )) for object_data in data
            ))
            replaced = self.for_datetime().filter(conditions)
        else:
            raise ValueError("Empty data set given and replace_all not specified. "
                             "Can neither expire old objects nor create new ones.")

        # Insert new objects:
        inserted = tuple(self.create(**object_data) for object_data in data)

        # Expire replaced objects:
        replaced.exclude(pk__in=[obj.pk for obj in inserted]).update(end_dt=timezone.now())

        # Return new objects:
        return inserted


class TransitoryObjectManager(base.ConfigurableManager):
    """Model manager supporting related objects which must be expired and replaced by
    fresh objects, rather than updated or deleted.

    It is assumed that models making use of this manager have a "start" DateTimeField
    and, more importantly, an "end" DateTimeField; the "end" field, when set, indicates
    that the object is no longer active.

    """
    @classmethod
    def configure(cls, instance, signature_fields=None, source_fields=None):
        instance.signature_fields = signature_fields
        instance.source_fields = source_fields
        return instance

    def get_query_set(self):
        return TransitoryObjectQuerySet.make(self)

    def for_datetime(self, *args, **kws):
        return self.get_query_set().for_datetime(*args, **kws)

    def source(self, *args, **kws):
        return self.get_query_set().source(*args, **kws)

    def replace(self, *args, **kws):
        return self.get_query_set().replace(*args, **kws)
