from django.db.models import Manager as BaseManager
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query import QuerySet as BaseQuerySet


class QuerySet(BaseQuerySet):

    def first_or_create(self, **kws):
        """Look up the first object in the set, creating a new one if necessary.

        Returns a tuple of (object, created), where "created" is a Boolean
        specifying whether an object was created.

        Note: If your schema enforces uniqueness for this query, this method
        will not protect against constraint violation. See instead get_or_create().

        """
        defaults = kws.pop('defaults', {})
        lookup = kws.copy()
        for field in self.model._meta.fields:
            try:
                lookup[field.name] = lookup.pop(field.attname)
            except KeyError:
                pass

        self._for_write = True
        obj = self.filter(**lookup).first()
        if obj is not None:
            return (obj, False)

        params = {key: value for (key, value) in kws.items() if LOOKUP_SEP not in key}
        params.update(defaults)
        obj = self.model(**params)
        obj.save(force_insert=True, using=self.db)
        return (obj, True)


class Manager(BaseManager):

    def get_queryset(self):
        return QuerySet(self.model, using=self._db)

    def first_or_create(self, **kws):
        try:
            core_filters = self.core_filters
        except AttributeError:
            pass
        else:
            # This is a RelatedManager -- update keywords with parent object
            for (filter_key, rel_obj) in core_filters.items():
                rel_field_name = filter_key.split(LOOKUP_SEP, 1)[0]
                kws[rel_field_name] = rel_obj

        return self.get_queryset().first_or_create(**kws)
