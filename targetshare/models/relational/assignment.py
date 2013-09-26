from django.db import models

from .manager import AssignedObjectQuerySet


class Assignment(models.Model):

    assignment_id = models.AutoField(primary_key=True)
    visit = models.ForeignKey('Visit', related_name='assignments')
    campaign = models.ForeignKey('Campaign', null=True, blank=True)
    content = models.ForeignKey('ClientContent', null=True, blank=True)
    feature_type = models.CharField(max_length=128, blank=True)
    feature_row = models.IntegerField(null=True, blank=True)
    random_assign = models.NullBooleanField()
    assign_dt = models.DateTimeField(auto_now_add=True)
    chosen_from_table = models.CharField(max_length=128, blank=True)
    chosen_from_rows = models.CharField(max_length=128, blank=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'assignments'

    @classmethod
    def make_managed(cls, visit, campaign, content, assignment,
             manager=None, options=None, random_assign=True):
        """Construct an Assignment instance from the given values.

            * At least one of `manager` and `options` is required
            * If `options` is not an AssignedObjectQuerySet, the AssignedObjectManager
              `manager` must be supplied
            * If `options` is not supplied at all, `chosen_from_rows` will be the
              queried, unfiltered, from the `manager`

        """
        # Determine feature_type and model:
        if isinstance(options, AssignedObjectQuerySet):
            feature_type = options.assigned_object
            model = options.model
        elif manager:
            feature_type = manager.assigned_object
            model = manager.model
        else:
            raise TypeError("Could not determine feature type; supply an "
                            "AssignedObjectQuerySet or AssignedObjectManager")

        if not feature_type.endswith('_id'):
            feature_type += '_id'

        # Determine chosen_from_rows:
        if options is None:
            if manager is None:
                raise TypeError("Could not determine Assignment options; "
                                "supply options or an object manager")
            chosen_from_rows = list(manager.values_list(feature_type, flat=True))
        elif isinstance(options, AssignedObjectQuerySet):
            chosen_from_rows = list(options.values_list(feature_type, flat=True))
        else:
            def cascade_getattr(obj):
                try:
                    return getattr(obj, feature_type)
                except AttributeError:
                    return getattr(obj, 'pk', obj)
            chosen_from_rows = [cascade_getattr(obj) for obj in options]

        return cls(
            visit=visit,
            campaign=campaign,
            content=content,
            feature_type=feature_type,
            feature_row=getattr(assignment, 'pk', assignment),
            random_assign=random_assign,
            chosen_from_table=model._meta.db_table,
            chosen_from_rows=chosen_from_rows,
        )
