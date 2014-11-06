import logging

from boto.dynamodb2.exceptions import ConditionalCheckFailedException
from boto.dynamodb2.items import NEWVALUE
from celery import shared_task
from django.core import serializers
from django.db import IntegrityError, transaction
from django.db.models import Model
from faraday import UpsertStrategy


LOG_RVN = logging.getLogger('crow')


@shared_task(ignore_result=True)
def bulk_create(objects):
    """Bulk-create objects belonging to a single model.

    Arguments:
        objects: A sequence of Models or Items

    """
    if not objects:
        return

    (model,) = {type(obj) for obj in objects}

    if issubclass(model, Model):
        for obj in objects:
            try:
                with transaction.atomic():
                    obj.save()
            except IntegrityError:
                (serialization,) = serializers.serialize('python', [obj])
                LOG_RVN.exception("bulk_create object save failed: %r", serialization)

    else:
        with model.items.batch_write() as batch:
            for obj in objects:
                batch.put_item(obj)


@shared_task(ignore_result=True)
def delayed_save(model_obj, **kws):
    """Save the given object in a background task process.

    Be aware that via this method, you can't guarantee the timing of the object
    save; so, this method is best reserved for things that don't need to be read
    back from the database "soon", and race conditions are possible. Use with some
    caution.

    Arguments:
        model_obj: A Django or boto model object

    Any remaining keyword arguments are passed to the object's save method.

    """
    model_obj.save(**kws)


@shared_task(ignore_result=True)
def get_or_create(model, *params, **kws):
    """Pass the given parameters to the model manager's get_or_create.

    May be invoked for a single object::

        get_or_create(User, username='john', defaults={'fname': 'John', 'lname': 'Smith'})

    ...or multiple at once::

        get_or_create(User,
            {'username': 'john', 'defaults': {'fname': 'John', 'lname': 'Smith'}},
            {'username': 'mary', 'defaults': {'fname': 'Mary', 'lname': 'May'}},
        )

    """
    if kws:
        params += (kws,)

    for paramset in params:
        try:
            model.objects.get_or_create(**paramset)
        except IntegrityError:
            LOG_RVN.exception("get_or_create failed: %r", paramset)


@shared_task(ignore_result=True)
def partial_save(item, _attempt=0):
    """Save the given boto Item in a background process, using its partial_save method.

    This task handles ConditionalCheckFailedExceptions from AWS, and in the event of a
    collision, attempts to merge the losing thread's novel data with that of the
    winning thread, before retrying via a new task.

    Arguments:
        item: A boto Item

    """
    try:
        item.partial_save()
    except ConditionalCheckFailedException:
        if _attempt == 4:
            LOG_RVN.exception(
                'Failed to handle save conflict on item %r', item.get_keys()
            )
            raise
    else:
        return

    # Attempt to resolve conflict:
    expected = item._orig_data
    fresh = type(item).items.get_item(**item.get_keys())
    for key, value in expected.items():
        fresh_value = fresh[key]
        unchanged = value == fresh_value
        novel = value is NEWVALUE and fresh_value is None
        if unchanged or novel:
            if key in item:
                fresh[key] = item[key]
            else:
                del fresh[key]

    partial_save.delay(fresh, _attempt + 1)


@shared_task(ignore_result=True)
def upsert(*items, **kws):
    """Upsert the given boto Items.

    Arguments:
        items: A sequence of boto Items to update, if they already exist in Dynamo,
            or to insert, if they don't.

            May be specified as a single sequence argument or as arbitrary
            anonymous arguments.

    """
    partial_save_queue = kws.get('partial_save_queue', 'partial_save')

    # Support single-argument sequence interface:
    if len(items) == 1 and isinstance(items[0], (list, tuple)):
        (items,) = items

    if len(items) == 0:
        # Nothing to upsert
        return

    try:
        (kls,) = {type(item) for item in items}
    except ValueError:
        raise TypeError("upsert cannot receive items of disparate type")

    unprocessed = {item.pk: item for item in items}

    # Update existing items:
    keys = [item.get_keys() for item in unprocessed.itervalues()]
    for existing in kls.items.batch_get(keys):
        item = unprocessed.pop(existing.pk)

        # Update the existing item:
        for (key, value) in item.items():
            field = kls._meta.fields.get(key)
            strategy = field.upsert_strategy if field else UpsertStrategy.overwrite
            strategy(existing, key, value)

        partial_save.apply_async(
            args=[existing],
            queue=partial_save_queue,
            routing_key=partial_save_queue.replace('_', '.'),
        )

    # Remaining items are new. Save them:
    for item in unprocessed.itervalues():
        partial_save.apply_async(
            args=[item],
            queue=partial_save_queue,
            routing_key=partial_save_queue.replace('_', '.'),
        )


@shared_task(task_time_limit=600, ignore_result=True)
def update_edges(edges):
    """Update edge tables.

    :arg edges: an instance of `models.datastructs.UserNetwork`

    """
    edges.write()
