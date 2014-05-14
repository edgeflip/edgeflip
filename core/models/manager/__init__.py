import sys

from django.db.models.query import QuerySet
from django.db import IntegrityError, models, transaction
from django.utils import six


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
