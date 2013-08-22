import celery
from boto.dynamodb2.items import Item, NEWVALUE
from boto.dynamodb2.exceptions import ConditionalCheckFailedException
from celery.utils.log import get_task_logger

from targetshare.models import dynamo


LOG = get_task_logger(__name__)


@celery.task
def bulk_create(objects):
    ''' Handles bulk create objects in the background, so that we're not
    stopping up the request/response cycle with irrelevant database writes.

    Arguments:
        objects: A list of model objects
    '''
    model, = set(type(obj) for obj in objects)
    model.objects.bulk_create(objects)


@celery.task
def delayed_save(model_obj, _attempt=0):
    ''' Very simple task for delaying the save() of an object for the
    background to keep the write out of the request/response cycle. Can
    certainly take new or existing objects, but keep in mind that this comes
    with a certain level of inherent danger.

    Via this method, you can't guarentee the timing of when the object is saved
    so this method is best reserved for things that won't need to be read back
    from the database in a very quick fashion. In other words, use with some
    appropriate level of caution

    '''
    if isinstance(model_obj, Item):
        _dynamo_partial_save(model_obj, attempt=_attempt)
    else:
        model_obj.save()


def _dynamo_partial_save(item, attempt):
    try:
        item.partial_save()
    except ConditionalCheckFailedException:
        if attempt == 4:
            LOG.exception(
                'Failed to handle save conflict on item %r', item._data
            )
            raise
    else:
        return

    # Attempt to resolve conflict:
    expected = item._orig_data
    fresh = item.table.get_item(**{
        key.name: item[key.name] for key in item.table.schema
    })
    for key, value in expected.items():
        fresh_value = fresh[key]
        unchanged = value == fresh_value
        novel = value is NEWVALUE and fresh_value is None
        if unchanged or novel:
            if key in item:
                fresh[key] = item[key]
            else:
                del fresh[key]

    delayed_save.delay(fresh, attempt + 1)


@celery.task
def bulk_upsert(items):
    """Upsert the given boto Items."""
    updated = dynamo.epoch_now()

    # TODO: add property to Item:
    def pk(item):
        return tuple(item.get_keys().values())

    items_data = {}
    for item in items:
        # TODO: move to pre-save (before building prepare_partial perhaps):
        item['updated'] = updated
        items_data[pk(item)] = item
    if not items_data:
        return

    (table,) = set(item.table for item in items)

    # Update existing items:
    # FIXME: result batching --J
    for existing in table.batch_get(keys=[item.get_keys() for item in items_data.values()]):
        item = items_data.pop(pk(existing))

        # update the existing item:
        for key, value in item.items():
            existing[key] = value

        delayed_save.delay(existing)

    # Remaining items are new. Save them:
    for item in items_data.values():
        delayed_save.delay(item)


@celery.task
def update_tokens(token):
    """update tokens table

        :arg token: a `datastruct.TokenInfo`

    """
    try:
        ownerId = int(token.ownerId)
    except (ValueError, TypeError):
        LOG.warn("Bad ownerId %r, token %s not updated", token.ownerId, token.tok)
    else:
        dynamo.save_token(ownerId, int(token.appId), token.tok, token.expires)


@celery.task
def update_edges(edges):
    """update edges table

    :arg edges: a list of `datastruct.Edge`

    """
    # pick out all the non-None EdgeCounts from all the edges
    counts = [c for e in edges for c in (e.countsIn, e.countsOut) if c is not None]
    dynamo.save_many_edges(
        {
            'fbid_source': count.sourceId,
            'fbid_target': count.targetId,
            'post_likes': count.postLikes,
            'post_comms': count.postComms,
            'stat_likes': count.statLikes,
            'stat_comms': count.statComms,
            'wall_posts': count.wallPosts,
            'wall_comms': count.wallComms,
            'tags': count.tags,
            'photos_target': count.photoTarget,
            'photos_other': count.photoOther,
            'mut_friends': count.mutuals,
        }
        for count in counts
    )


def update_database(user, token, edges):
    """async version of `edgeflip.database_compat.updateDb"""
    tasks = []
    tasks.append(update_tokens.delay(token))
    tasks.append(bulk_upsert.delay([user.to_dynamo()] +
                                   [edge.secondary.to_dynamo() for edge in edges]))
    tasks.append(update_edges.delay(edges))
    ids = [t.id for t in tasks]

    LOG.debug("updateDb() using background celery tasks %r for user %d", ids, user.id)
