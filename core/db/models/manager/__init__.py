from django.db.models import Manager as BaseManager
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query import QuerySet as BaseQuerySet

from core.db import locking
from core.db.models import sql


class NullContextManager(object):

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_value, traceback):
        return None

Unmanaged = NullContextManager()


class QuerySet(BaseQuerySet):

    def lock(self, prefix='', timeout=None):
        return QuerySetLock(self, prefix, timeout)

    def first_or_create(self, **kws):
        """Look up the first object in the set, creating a new one if necessary.

        Returns a tuple of (object, created), where "created" is a Boolean
        specifying whether an object was created.

        Note: If your schema enforces uniqueness for this query, this method
        will not protect against constraint violation. See instead get_or_create().

        """
        defaults = kws.pop('defaults', {})
        lock = kws.pop('lock', None)
        lookup = kws.copy()
        for field in self.model._meta.fields:
            try:
                lookup[field.name] = lookup.pop(field.attname)
            except KeyError:
                pass

        self._for_write = True
        queryset = self.filter(**lookup)

        # Use advisory lock so long as none is active, unless overridden by parameter
        should_lock = self.db not in QuerySetLock.context.managed if lock is None else lock

        with (queryset.lock() if should_lock else Unmanaged):
            obj = queryset.first()
            if obj is not None:
                return (obj, False)

            params = {key: value for (key, value) in kws.items() if LOOKUP_SEP not in key}
            params.update(defaults)
            obj = self.model(**params)
            obj.save(force_insert=True, using=self.db)
            return (obj, True)


class QuerySetLock(locking.AdvisoryLock):

    def __init__(self, queryset, prefix='', timeout=None):
        query_hash = sql.hash_query(queryset.query)
        nickname = prefix + query_hash
        super(QuerySetLock, self).__init__(nickname, using=queryset.db, timeout=timeout)
        self.queryset = queryset

    def __enter__(self):
        super(QuerySetLock, self).__enter__()
        return self.queryset


class Manager(BaseManager):

    def get_queryset(self):
        return QuerySet(self.model, using=self._db)

    def first_or_create(self, **kws):
        try:
            core_filters = self.core_filters
        except AttributeError:
            pass
        else:
            # This is a descendant RelatedManager -- update params with
            # reference to parent object.
            # RelatedManager.get_queryset will add the filter to the look-up;
            # rather than duplicate the condition there, reserve it for the
            # create, via "defaults":
            defaults = kws.setdefault('defaults', {})
            for (filter_key, rel_obj) in core_filters.iteritems():
                rel_field_name = filter_key.split(LOOKUP_SEP, 1)[0]
                defaults[rel_field_name] = rel_obj

        return self.get_queryset().first_or_create(**kws)
