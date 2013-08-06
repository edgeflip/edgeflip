import datetime
from collections import defaultdict

from django.db import models


class StartStopManager(models.Manager):

    def __init__(self):
        super(StartStopManager, self).__init__()
        meta = self.model._meta
        self.ss_fields = meta.ss_fields
        self.ss_end_field = getattr(meta, 'ss_end_field', 'end_dt')

    def replace(self, data, replace_all=False):
        """Replace the RelatedManager's active objects with new objects as specified by
        an iterable of new associated object data.

        By default, pre-existing, active objects whose signatures conflict with the
        objects to be inserted are expired by setting a DateTimeField (defaulting to
        "end_dt") to the current datetime. Pass the `replace_all` flag to expire all
        associated objects.

        For example::

            class Filter(models.Model):
                ...

            class FilterFeature(models.Model):
                filter = models.ForeignKey(Filter)
                feature = models.CharField()
                operator = models.CharField()
                start_dt = models.DateTimeField(auto_now_add=True)
                end_dt = models.DateTimeField(null=True)

                class Meta(object):
                    ss_fields = 'feature', 'operator'

            my_filter = Filter.objects.get(pk=1)
            my_filter.filterfeature_set.replace([
                {'feature': 'foo', operator: 'min'},
                {'feature': 'foo', operator: 'max'},
                {'feature': 'bar', operator: 'min'},
            ])

        As called above, `replace`:

            1) validates that unique `FilterFeature`s are being inserted, where
                the object signature is determined by `FilterFeature`'s
                `Meta.ss_fields`
            2) expires the currently active set of `FilterFeature`s whose
                signatures match those to be inserted by setting `end_dt`
            3) inserts the new `FilterFeature`s under `my_filter`

        Alternatively, `replace_all` may be specified, such that all active
        `FilterFeature`s are expired and replaced by the new data::

            my_filter.filterfeature_set.replace(
                [
                    {'feature': 'foo', operator: 'min'},
                    {'feature': 'foo', operator: 'max'},
                    {'feature': 'bar', operator: 'min'},
                ],
                replace_all=True,
            )

        """
        # Avoid accidental application to all instances of parent model:
        if not getattr(self, 'instance', None):
            raise TypeError("replace intended for use on related managers")

        # Check new data uniqueness:
        signatures = defaultdict(lambda: 0)
        for object_data in data:
            signatures[tuple(object_data[field] for field in self.ss_fields)] += 1
        object_data_dupes = tuple(
            signature for signature, count in signatures.items() if count > 1
        )
        if object_data_dupes:
            raise ValueError(
                "Associated objects must be unique on columns {!r}. "
                "Duplicates found for {!r}".format(self.ss_fields, object_data_dupes)
            )

        # Determine related objects to replace:
        if replace_all:
            replaced = self.filter(**{self.ss_end_field: None})
        else:
            # Objects to replace match all columns in fields (&) for any set
            # of data (|):
            conditions = reduce(set.union, ( # |
                reduce(set.intersection, ( # &
                    models.Q(**{field: object_data[field]}) for field in self.ss_fields
                )) for object_data in data
            ))
            replaced = self.filter(conditions, **{self.ss_end_field: None})

        # Expire replaced objects:
        replaced.update(**{self.ss_end_field: datetime.datetime.now()})

        # Insert and return new objects:
        return tuple(self.create(**object_data) for object_data in data)
