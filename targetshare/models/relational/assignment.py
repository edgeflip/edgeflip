from django.db import models
from django.utils.functional import cached_property

from core.models.manager import RepeatableReadQuerySet


class AssignmentQuerySet(RepeatableReadQuerySet):

    def create_managed(self, **kws):
        obj = self.model.make_managed(**kws)
        self._for_write = True
        obj.save(force_insert=True, using=self.db)
        return obj


class AssignmentManager(models.Manager):

    @cached_property
    def related_objects_descriptor(self):
        try:
            instance = self.instance
        except AttributeError:
            return None

        for key, value in vars(type(instance)).items():
            manager_cls = getattr(value, 'related_manager_cls', None)
            if isinstance(self, manager_cls):
                return value

    def create_managed(self, **kws):
        if self.related_objects_descriptor:
            kws[self.related_objects_descriptor.related.field.name] = self.instance
        return self.get_query_set().create_managed(**kws)

    def get_query_set(self):
        return AssignmentQuerySet(self.model, using=self._db)


class AssignmentModel(models.Model):

    campaign = models.ForeignKey('Campaign', null=True, blank=True)
    content = models.ForeignKey('ClientContent', null=True, blank=True)
    feature_type = models.CharField(max_length=128, blank=True)
    feature_row = models.IntegerField(null=True, blank=True)
    random_assign = models.NullBooleanField()
    assign_dt = models.DateTimeField(auto_now_add=True)
    chosen_from_table = models.CharField(max_length=128, blank=True)
    chosen_from_rows = models.CharField(max_length=128, blank=True)

    objects = AssignmentManager()

    class Meta(object):
        abstract = True

    @classmethod
    def make_managed(cls, feature_row, chosen_from_rows,
                     manager=None, feature_type=None, random_assign=True, **kws):
        """Construct an Assignment object from the given values.

        `chosen_from_rows` must be an AssignedObjectQuerySet, an
        AssignedObjectManager, or None -- if None, the `manager` argument is
        required, specifying the AssignedObjectManager.

        Features:

            *) `feature_row` may be the primary key or the assigned model object
            *) `chosen_from_rows` may be the QuerySet or Manager of the assigned object
            *) `chosen_from_table` is determined automatically
            *) `feature_type` is determined automatically (if unspecified)
            *) Assignment attributes such as `campaign` and `content` cannot be guessed,
                but are passed through

        """
        if manager is None and chosen_from_rows in ('', None):
            raise TypeError("Either chosen_from_rows or manager must not be empty")

        # Determine feature_type and table:
        if manager is None:
            feature_type1 = chosen_from_rows.assigned_object
            chosen_from_table = chosen_from_rows.model._meta.db_table
        else:
            feature_type1 = manager.assigned_object
            chosen_from_table = manager.model._meta.db_table
        feature_type1 = getattr(feature_type1, 'name', feature_type1)
        if not feature_type1.endswith('_id'):
            feature_type1 += '_id'

        if chosen_from_rows is None:
            chosen_from_rows = ''
        elif not isinstance(chosen_from_rows, (basestring, list)):
            try:
                values = chosen_from_rows.values_list('pk', flat=True)
            except AttributeError:
                values = chosen_from_rows
            chosen_from_rows = list(values)

        return cls(
            feature_type=feature_type or feature_type1,
            feature_row=getattr(feature_row, 'pk', feature_row),
            chosen_from_table=chosen_from_table,
            chosen_from_rows=chosen_from_rows,
            random_assign=random_assign,
            **kws
        )


class Assignment(AssignmentModel):

    assignment_id = models.AutoField(primary_key=True)
    visit = models.ForeignKey('Visit', related_name='assignments')

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'assignments'


class NotificationAssignment(AssignmentModel):

    notification_assignment_id = models.AutoField(primary_key=True)
    notification_user = models.ForeignKey('NotificationUser', related_name='assignments')

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'notification_assignments'
