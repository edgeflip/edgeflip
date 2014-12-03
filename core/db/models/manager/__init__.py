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
        """Construct a QuerySetLock from this QuerySet.

        QuerySetLock wraps a QuerySet in an AdvisoryLock, which is automatically
        named according to the QuerySet's collected query conditions. This way,
        a block of database-interacting code, whose query cannot be constrained
        at the database level, can eliminate its race condition.

        In the below examples, a BlogEvent model has a foreign key to an Author
        model:

            class Author(Model):
                username = CharField(max_length=30)

            class BlogEvent(Model):
                author = ForeignKey(Author)
                event_type = SlugField()

        The code below has a race condition:

            if not author.blogevent_set.filter(event_type='joined').exists():
                author.blogevent_set.create(event_type='joined')

        What's wrong with the code above? Multiple threads may hit the above,
        and (near-simultaneously) create multiple BlogEvents for 'joined'. The
        ideal solution might be a unique key on
        `(BlogEvent.author_id, BlogEvent.event_type)`; however, this isn't
        practical for all schema, for example if we'd like our BlogEvent table
        to also support the 'post' event type, which *must* allow duplicates.

        Instead, we can wrap the offending code in an AdvisoryLock:

            join_events = author.blogevent_set.filter(event_type='joined')
            with join_events.lock():
                if not join_events.exists():
                    author.blogevent_set.create(event_type='joined')

        Now, before initiating the block, competing threads must acquire an
        advisory lock from the database; the winning thread's lock blocks other
        threads, until after the BlogEvent has been created, (if necessary).

        The wrapped QuerySet is returned to contexts managed by QuerySetLock,
        allowing us to streamline the above:

            with author.blogevent_set.filter(event_type='joined').lock() as join_events:
                if not join_events.exists():
                    author.blogevent_set.create(event_type='joined')

        Note that the situation described above is not helped by
        `get_or_create`, which itself relies upon constraints set at the
        database level. See instead: `first_or_create`.

        """
        return QuerySetLock(self, prefix, timeout)

    def first_or_create(self, **kws):
        """Look up the first object in the set, creating a new one if necessary.

        Returns a tuple of (object, created), where "created" is a Boolean
        specifying whether an object was created.

        Note: If your schema enforces uniqueness for this query, this method
        will not protect against constraint violation. See instead get_or_create().

        By default, if no AdvisoryLock is active for the QuerySet database's
        connection, this method initiates a lock, via `QuerySet.lock`. To
        require a lock, (raising an exception if a conflicting lock is already
        acquired), specify the parameter `lock=True`. To disable locking,
        specify `lock=False`.

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
    """AdvisoryLock constructed from a QuerySet."""

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
