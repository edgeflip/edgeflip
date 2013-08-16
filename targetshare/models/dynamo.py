"""tools & classes for data stored in AWS DynamoDB

.. envvar:: dynamo.prefix

    String prefix to prepend to table names. A `.` is used as a separtor

.. envvar:: dynamo.engine

    Which engine to use. One of 'aws', 'mock'.

This module makes heavy use of iterators and generator comprehensions.
Results are processed in Python as a stream from AWS. This makes things fast
and keeps memory usage low. Many functions return generators instead of
lists. Ideally, you should materialize these (i.e., iterate through/list())
as late as possible in your code.

There are three data types managed by this module: users, tokens and edges.
All objects have a `udpated` field, which is the timestamp the object was
last stored to Dynamo.

Users
+++++

Users are stored in a single table keyed by `fbid`. They have various fields
(see `save_user` for a list). All fields are strings and optional, except for `fbid` which
is a number and `birthday` which is a date.


Tokens
+++++

Tokens are stored in a single table keyed by `(fbid, appid)`. All fields are
required. `token` is the string auth token from Facebook. `expires` is a
datetime when the token expires.


Edges
+++++

Edges are stored in two tables: `edges_incoming`, which is keyed by `(target, source)`, and `edges_outgoing`, which is keyed by `(source, target)`. All fields are ints and optional (see `save_incoming_edge` for a list). Your code should always use `save_edge` / `save_many_edges`.

Field data lives in the incoming table; fetching outgoing edges requires a
join to access the data. Both tables also have a local secondary index on
`(fbid, updated)` which is used to restrict freshness to be newer than a
given date.

"""
from __future__ import print_function
import calendar
import logging
import threading
import pymlconf
import time
import types
import datetime
import sys
from itertools import imap

from boto.regioninfo import RegionInfo
from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.dynamodb2.table import Table
from boto.dynamodb2.items import Item
from boto.dynamodb2.fields import HashKey, RangeKey, IncludeIndex
from boto.dynamodb2.types import NUMBER
from django.conf import settings
from django.utils import timezone


LOG = logging.getLogger(__name__)

SCHEMAS = {} # map of table name => boto schema dict


def _make_dynamo_aws():
    """Make a connection to dynamo, based on configuration. For internal use.

    :rtype: dynamo connection object

    """
    try:
        access_id = settings.AWS.AWS_ACCESS_KEY_ID
        secret = settings.AWS.AWS_SECRET_ACCESS_KEY
    except (KeyError, pymlconf.ConfigurationError):
        access_id = None
        secret = None
    return DynamoDBConnection(aws_access_key_id=access_id,
                              aws_secret_access_key=secret)


def _make_dynamo_mock():
    """Make a connection to the mock dynamo server, based on configuration. For internal use.

    :rtype: dynamo connection object

    """
    # based on https://ddbmock.readthedocs.org/en/v0.4.1/pages/getting_started.html#run-as-regular-client-server
    host = 'localhost'
    port = settings.DYNAMO.get('port') or 4567
    endpoint = '{}:{}'.format(host, port)
    region = RegionInfo(name='mock', endpoint=endpoint)
    conn = DynamoDBConnection(aws_access_key_id="AXX", aws_secret_access_key="SEKRIT", region=region, port=port, is_secure=False)
    # patch the region_name so boto doesn't explode
    conn._auth_handler.region_name = "us-mock-1"
    return conn


def _make_dynamo():
    """Retrive a [mock] dynamo server connection, based on configuration. For internal use."""
    if settings.DYNAMO.engine == 'aws':
        return _make_dynamo_aws()
    elif settings.DYNAMO.engine == 'mock':
        return _make_dynamo_mock()
    raise RuntimeError("Bad value {} for settings.DYNAMO.engine".format(settings.DYNAMO.engine))


class DynamoDBConnectionProxy(object):
    """A lazily-connecting, thread-local proxy to a dynamo server connection."""
    _threadlocal = threading.local()

    @classmethod
    def get_connection(cls):
        try:
            return cls._threadlocal.dynamo
        except AttributeError:
            cls._threadlocal.dynamo = _make_dynamo()
            return cls._threadlocal.dynamo

    # Specify type(self) when calling get_connection to avoid reference to
    # any same-named method on proxied object:
    def __getattr__(self, name):
        return getattr(type(self).get_connection(), name)

    def __setattr__(self, name, value):
        return setattr(type(self).get_connection(), name, value)

connection = DynamoDBConnectionProxy()


def _table_name(name):
    """return a table name using the prefix specified in config.

    For internal use.
    """
    return ".".join((settings.DYNAMO.prefix, name))


def get_table(name):
    """Return a boto table for the given name

    :rtype: `boto.dynamodb2.table.Table`
    """
    return Table(_table_name(name),
                 schema=SCHEMAS[name]['schema'],
                 indexes=SCHEMAS[name].get('indexes', []),
                 connection=connection)


def to_epoch(date):
    """Given a datetime.date or datetime.datetime, return seconds since the
    epoch in UTC.

    """
    if date is None:
        return None
    if isinstance(date, datetime.datetime):
        # Handle datetime timezones:
        return calendar.timegm(date.utctimetuple())
    # Naively convert time-less date:
    return time.mktime(date.timetuple())


def epoch_to_datetime(epoch):
    """given seconds since the epoch in UTC, return a timezone-aware datetime"""
    if epoch is None:
        return None
    return datetime.datetime.fromtimestamp(epoch, timezone.utc)


def epoch_to_date(epoch):
    """given seconds since the epoch, return a date"""
    if epoch is None:
        return None
    return datetime.date.fromtimestamp(epoch)


def epoch_now():
    """return the current UTC time as seconds since the epoch"""
    return to_epoch(timezone.now())


def _remove_null_values(dict_):
    """Modify a dict in place by deleting items having null-ish values. For internal use."""
    considered_types = (basestring, set, tuple, list, dict, types.NoneType)
    for key, value in dict_.items():
        if isinstance(value, considered_types) and not value:
            del dict_[key]


def create_table(**schema):
    """create a new table in Dynamo

    :arg dict schema: keyword args for `boto.dynamodb2.Table.create`

    """
    name = _table_name(schema['table_name'])
    LOG.info("Creating table %s", name)
    schema['table_name'] = name
    return Table.create(connection=connection, **schema)


def create_all_tables(timeout=0, wait=2, console=sys.stdout):
    """Create all tables in Dynamo.

    Table creation commands cannot be issued for two tables with secondary keys at
    once, and so commands are issued in order, and job status polled, to finish as
    quickly as possible without error.

    You should only have to call this method once.

    """
    if timeout < 0:
        raise ValueError("Invalid creation timeout")

    # Sort schemas so as to create those tables with secondary keys last:
    def sort_key(defn):
        _table_name, schema = defn
        return len(schema['schema'])
    schemas = sorted(SCHEMAS.items(), key=sort_key)

    for table_number, (table_name, schema) in enumerate(schemas, 1):
        # Issue creation directive to AWS:
        table = create_table(**schema)

        # Monitor job status:
        console.write("Table '{}' status: ".format(table_name))
        for count in xrange(timeout + 1):
            # Retrieve status:
            description = table.describe()
            status = description['Table']['TableStatus']

            # Update console:
            if count > 0:
                console.write(".")
            if count == 0 or status != 'CREATING':
                console.write(status)
            console.flush()

            if (
                status != 'CREATING' or         # Creation completed
                len(schema['schema']) == 1 or   # Still processing non-blocking tables
                table_number == len(schemas)    # This is the last table anyway
            ):
                break # We're done, proceed

            if count < timeout:
                time.sleep(wait)

        print('', file=console) # Break line


def drop_all_tables():
    """Delete all tables in Dynamo"""
    for table in SCHEMAS:
        try:
            get_table(table).delete()
        except StandardError:
            LOG.warn("Error deleting table %s", table, exc_info=True)
        else:
            LOG.debug("Deleted table %s", table)


##### USERS #####

SCHEMAS['users'] = {
    'table_name': 'users',
    'schema': [
        HashKey('fbid', data_type=NUMBER),
    ],
    'indexes': [],
}


def save_user(fbid, fname, lname, email, gender, birthday, city, state, updated=None):
    """save a user to Dynamo. If user exists, update with new, non-None attrs.

    :arg int fbid: the user's facebook id

    Other args are string or None. You can pass a value for `updated` but it will be replaced with current timestamp.
    """
    updated = epoch_now()
    birthday = to_epoch(birthday)

    data = locals()
    _remove_null_values(data)

    table = get_table('users')
    user = table.get_item(fbid=fbid)

    if user['fbid'] is None:
        # new user
        table.put_item(data)
    else:
        # update existing user. Don't even touch keys (which are unchanged)
        # because AWS/boto freak out
        for k, v in data.iteritems():
            if k != 'fbid':
                user[k] = v
        return user.partial_save()


def save_many_users(users):
    """save many users to Dynamo as a batch, overwriting existing rows.

    This modifies dicts passed in.

    :arg dicts users: iterable of dicts describing user. Keys should be as for `save_user`.
    """
    updated = epoch_now()
    table = get_table('users')
    with table.batch_write() as batch:
        for d in users:
            d['birthday'] = to_epoch(d.get('birthday'))
            d['updated'] = updated
            _remove_null_values(d)
            batch.put_item(data=d)


def update_many_users(users):
    """save many users to Dynamo as a batch, updating existing rows.

    This modifies dicts passed in.

    :arg dicts users: iterable of dicts describing user. Keys should be as for `save_user`.
    """
    updated = epoch_now()
    table = get_table('users')

    # map of fbid => data dict
    users_data = {u['fbid']: u for u in users}
    if not users_data:
        return

    for item in table.batch_get(keys=[{'fbid': k} for k in users_data]):
        if item['fbid'] is None:
            continue

        # pop the corresponding data dict
        data = users_data.pop(item['fbid'])
        data['birthday'] = to_epoch(data.get('birthday'))
        data['updated'] = updated
        _remove_null_values(data)

        # update the boto item
        for k, v in data.iteritems():
            if k != 'fbid':
                item[k] = v
        item.partial_save()

    # everything left in users_data must be new items. Loop through these &
    # save individually, so that a concurrent write will cause an error
    # (instead of silently clobbering using batch_write)
    for data in users_data.itervalues():
        data['birthday'] = to_epoch(data.get('birthday'))
        data['updated'] = updated
        _remove_null_values(data)
        table.put_item(data)


def fetch_user(fbid):
    """Fetch a user. Returns None if user not found.

    :arg int fbid: the users' Facebook ID
    :rtype: dict
    """
    table = get_table('users')
    x = table.get_item(fbid=int(fbid))
    if x['fbid'] is None:
        return None
    return _make_user(x)


def fetch_many_users(fbids):
    """Retrieve many users.

    :arg ids: list of facebook ID's
    :rtype: iterator of dict
    """
    table = get_table('users')
    # boto's BatchGetResultSet requires keys to be a list
    keys = [{'fbid': int(i)} for i in fbids]
    if not keys:
        return ()
    LOG.debug("Retrieving %d users", len(keys))
    results = table.batch_get(keys=keys)
    users = (_make_user(x) for x in results if x['fbid'] is not None)
    return users


def _make_user(x):
    """make a dict from a boto Item. for internal use"""
    u = dict(x.items())
    if 'birthday' in x:
        u['birthday'] = epoch_to_datetime(x['birthday'])
    u['updated'] = epoch_to_datetime(x['updated'])
    return u


##### TOKENS #####

SCHEMAS['tokens'] = {
    'table_name': 'tokens',
    'schema': [
        HashKey('fbid', data_type=NUMBER),
        RangeKey('appid', data_type=NUMBER)
    ]
}


def save_token(fbid, appid, token, expires, updated=None):
    """save a token to dynamo, overwriting existing.

    :arg int fbid: the facebook id
    :arg int appid: the app's id
    :arg str token: the auth token from facebook
    :arg datetime expires: when the token expires, in GMT
    :arg updated: you can pass a value you, but it will be
                  replaced with current timestamp.
    """
    table = get_table('tokens')
    x = Item(table, data=dict(
        fbid=int(fbid),
        appid=int(appid),
        token=token,
        expires=to_epoch(expires),
        updated=epoch_now()
    ))
    return x.save(overwrite=True)


def fetch_token(fbid, appid):
    """retrieve a token from facebook

    :arg int fbid: the facebook id
    :arg int appid: the app's id
    :rtype: dict or None if not found
    """
    table = get_table('tokens')
    x = table.get_item(fbid=int(fbid), appid=int(appid))
    if x['fbid'] is None:
        return None
    return _make_token(x)


def fetch_many_tokens(ids):
    """Retrieve many tokens.

    :arg ids: list of (facebook ID, app ID)
    :rtype: iterator of dict
    """
    table = get_table('tokens')
    # boto's BatchGetResultSet requires a list for keys
    keys = [{'fbid': i, 'appid': a} for i, a in ids]
    if not keys:
        return ()
    LOG.debug('Retrieving %d tokens', len(keys))
    results = table.batch_get(keys=keys)
    tokens = (_make_token(x) for x in results if x['fbid'] is not None)
    return tokens


def _make_token(x):
    """make a dict from a boto Item. for internal use"""
    t = dict(x.items())
    t['expires'] = epoch_to_datetime(t['expires'])
    t['updated'] = epoch_to_datetime(t['updated'])
    return t


##### EDGES #####

SCHEMAS['edges_outgoing'] = {
    'table_name': 'edges_outgoing',
    'schema': [
        HashKey('fbid_source', data_type=NUMBER),
        RangeKey('fbid_target', data_type=NUMBER)
    ],
    'indexes': [
        IncludeIndex('updated',
                     parts=[HashKey('fbid_source', data_type=NUMBER),
                            RangeKey('updated', data_type=NUMBER)],
                     includes=['fbid_target', 'fbid_source']),
    ]
}

SCHEMAS['edges_incoming'] = {
    'table_name': 'edges_incoming',
    'schema': [
        HashKey('fbid_target', data_type=NUMBER),
        RangeKey('fbid_source', data_type=NUMBER)
    ],
    'indexes': [
        IncludeIndex('updated',
                     parts=[HashKey('fbid_target', data_type=NUMBER),
                            RangeKey('updated', data_type=NUMBER)],
                     includes=['fbid_target', 'fbid_source']),
    ]
}


def save_edge(fbid_source, fbid_target, **kwargs):
    """Save an edge to dynamo

    :arg int fbid_source: the source's -> facebook id
    :arg int fbid_target: the -> target's facebook id

    Keyword args int or None, as passed to `save_incoming_edge`. You can pass
    a value for updated, but it will be replaced with a current timestamp.
    """

    kwargs['updated'] = updated = epoch_now()
    save_incoming_edge(fbid_source, fbid_target, **kwargs)
    save_outgoing_edge(fbid_source, fbid_target, updated)


def save_many_edges(edges):
    """save many edges to dynamo in a batch, overwriting.

    YMMV for consistency. This modifies dicts passed in.

    :arg dicts edges: iterable of dicts describing edges. Keys should be as for `save_edge`.
    """
    updated = epoch_now()
    incoming = get_table('edges_incoming')
    outgoing = get_table('edges_outgoing')

    with incoming.batch_write() as inc, outgoing.batch_write() as out:
        for e in edges:
            e['updated'] = updated
            _remove_null_values(e)
            inc.put_item(data=e)
            out.put_item(data={'fbid_source': e['fbid_source'], 'fbid_target': e['fbid_target'], 'updated': updated})


def save_incoming_edge(fbid_source, fbid_target, post_likes, post_comms, stat_likes, stat_comms, wall_posts, wall_comms, tags, photos_target, photos_other, mut_friends, updated):
    """save an incoming edge and its attributes to dynamo, updating.

    You should probably use `save_edge` in your code instead.

    :arg int fbid_source: the source's -> facebook id
    :arg int fbid_target: the -> target's facebook id

    Other args int or None.
    """
    data = locals()
    _remove_null_values(data)

    t = 'edges_incoming'
    table = get_table(t)
    x = table.get_item(fbid_source=fbid_source, fbid_target=fbid_target)
    if x['fbid_source'] is None:
        # new edge
        LOG.debug("Saving new edge %s -> %s to table %s", fbid_source, fbid_target, t)
        table.put_item(data)
    else:
        # update existing edge. Don't even touch keys (which are
        # unchanged) because AWS/boto freak out
        LOG.debug("Updating edge %s -> %s in table %s", fbid_source, fbid_target, t)
        for k, v in data.iteritems():
            if k not in ('fbid_source', 'fbid_target'):
                x[k] = v
        x.partial_save()


def save_outgoing_edge(fbid_source, fbid_target, updated):
    """save an outgoing edge to dynamo, overwrites

    You should probably use `save_edge` in your code instead.

    :arg int fbid_source: the source's -> facebook id
    :arg int fbid_target: the -> target's facebook id
    :arg epoch updated: the timestamp
    """
    data = locals()

    t = 'edges_outgoing'
    table = get_table(t)
    LOG.debug("Saving edge %s -> %s to table %s", fbid_source, fbid_target, t)
    table.put_item(data, overwrite=True)


def fetch_edge(fbid_source, fbid_target):
    """retrieve an edge from facebook

    :arg int fbid_source: the source's -> facebook id
    :arg int fbid_target: the -> target's facebook id
    :rtype: dict or None if not found
    """
    t = 'edges_incoming'
    table = get_table(t)
    x = table.get_item(fbid_source=fbid_source, fbid_target=fbid_target)
    return _make_edge(x) if x['fbid_source'] is not None else None


def fetch_many_edges(ids):
    """Retrieve many edges.

    :arg ids: list of (source ID, target ID)
    :rtype: iterator of dict
    """
    table = get_table('edges_incoming')
    # Boto's BatchGetResultSet requires a list for keys
    keys = [{'fbid_source': s, 'fbid_target': t} for s, t in ids]
    if not keys:
        return ()
    LOG.debug('Retrieving %d edges', len(keys))
    results = table.batch_get(keys=keys)
    edges = (_make_edge(x) for x in results if x['fbid_source'] is not None)
    return edges


def fetch_all_incoming_edges():
    """Retrieve all incoming edges from dynamo

    WARNING: this does a full scan and is SLOW & EXPENSIVE

    :rtype: iter of dict
    """
    return imap(_make_edge, get_table('edges_incoming').scan())


def fetch_incoming_edges(fbid, newer_than=None):
    """Fetch many incoming edges

    select all edges where target == $fbid
    (and optionally) where updated > now() - $newer_than

    :arg int fbid: target facebook id
    :arg `datetime.datetime` newer_than: only include edges newer than this
    :rtype: iter of dict
    """
    fbid = int(fbid)
    table = get_table('edges_incoming')
    if newer_than is None:
        results = table.query(fbid_target__eq=fbid)
        return imap(_make_edge, results)
    else:
        keys = table.query(index='updated',
                           fbid_target__eq=fbid,
                           updated__gt=to_epoch(newer_than))
        return fetch_many_edges((k['fbid_source'], k['fbid_target']) for k in keys)


def fetch_outgoing_edges(fbid, newer_than=None):
    """Fetch many outgoing edges

    select all edges where source == $fbid
    (and optionally) where updated > now() - $newer_than

    :arg int fbid: source facebook id
    :arg `datetime.datetime` newer_than: only include edges newer than this
    :rtype: iter of dict
    """
    fbid = int(fbid)
    table = get_table('edges_outgoing')
    if newer_than is None:
        keys = table.query(fbid_source__eq=fbid)
    else:
        keys = table.query(index='updated',
                           fbid_source__eq=fbid,
                           updated__gt=to_epoch(newer_than))

    return fetch_many_edges((k['fbid_source'], k['fbid_target']) for k in keys)


def _make_edge(x):
    """make a dict from a boto Item. for internal use"""
    e = dict(x.items())
    e['updated'] = epoch_to_datetime(e['updated'])
    return e
