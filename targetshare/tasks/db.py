import celery
import logging
from boto.dynamodb2.items import NEWVALUE
from boto.dynamodb2.exceptions import ConditionalCheckFailedException
from celery.utils.log import get_task_logger

from targetshare import models


rvn_logger = logging.getLogger('crow')

@celery.task
def bulk_create(objects):
    """Bulk-create objects in a background task process.

    Arguments:
        objects: A sequence of model objects

    """
    (model,) = set(type(obj) for obj in objects)
    model.objects.bulk_create(objects)


@celery.task
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


@celery.task
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
            rvn_logger.exception(
                'Failed to handle save conflict on item %r', dict(item)
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


@celery.task
def upsert(*items):
    """Upsert the given boto Items.

    Arguments:
        items: A sequence of boto Items to update, if they already exist in Dynamo,
            or to insert, if they don't.

            May be specified as a single sequence argument or as arbitrary
            anonymous arguments.

    """
    # Support single-argument sequence interface:
    if len(items) == 1 and isinstance(items[0], (list, tuple)):
        (items,) = items

    items_data = {item.pk: item for item in items}
    if not items_data:
        return

    (cls,) = set(type(item) for item in items)
    keys = [item.get_keys() for item in items_data.values()]

    # Update existing items:
    for existing in cls.items.batch_get(keys=keys):
        item = items_data.pop(existing.pk)

        # update the existing item:
        for key, value in item.items():
            existing[key] = value

        partial_save.delay(existing)

    # Remaining items are new. Save them:
    for item in items_data.values():
        partial_save.delay(item)


@celery.task(task_time_limit=600)
def update_edges(edges):
    """Update edge tables.

    :arg edges: an iterable of `datastruct.Edge`

    """
    models.datastructs.Edge.write(edges)
