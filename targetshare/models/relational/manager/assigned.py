from targetshare import utils

from . import transitory


class AssignedObjectQuerySet(transitory.TransitoryObjectQuerySet):

    def random_assign(self):
        """Return a randomly-selected object from the QuerySet.

        Requires that the QuerySet has been configured with an `assigned_object` field:
        the objects' related model field to be assigned.

        The objects' model must also have a `rand_cdf` field, the CDF probability of
        the object.

        """
        assigned_object = getattr(self, 'assigned_object', None)
        if not assigned_object:
            raise TypeError("Assigned object field not set")
        assigned_object = getattr(assigned_object, 'name', assigned_object)

        for field in self.model._meta.fields:
            if field.name == assigned_object:
                assigned_class = field.related.parent_model
                break
        else:
            raise TypeError("Field {!r} not found on model {meta.app_label}.{meta.object_name}"
                            .format(assigned_object, meta=self.model._meta))

        options = self.values_list(assigned_object, 'rand_cdf')
        object_id = utils.random_assign(options)
        return assigned_class.objects.get(pk=object_id)


class AssignedObjectManager(transitory.TransitoryObjectManager):

    def configure(self, instance, assigned_object, signature_fields=None, source_fields=None):
        super(AssignedObjectManager, self).configure(instance, signature_fields, source_fields)
        instance.assigned_object = assigned_object

    def get_query_set(self):
        return AssignedObjectQuerySet.make(self)

    def random_assign(self):
        return self.get_query_set().random_assign()
