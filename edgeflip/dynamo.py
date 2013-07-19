#!/usr/bin/env python
"""
tools & classes for data stored in AWS DynamoDB

.. envvar:: dynamo.prefix

    String prefix to prepend to table names. A `.` is used as a separtor

.. envvar:: dynamo.engine

    Which engine to use. One of 'aws', 'mock'.

The fetch_* methods return iterators yielding objects from `datastructs`.
They could easily be converted to yield raw boto Items or another object
"""
import logging
import threading
import flask
import pymlconf
import time
import datetime
from itertools import imap, chain
from more_itertools import chunked

from boto.regioninfo import RegionInfo
from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.dynamodb2.table import Table
from boto.dynamodb2.items import Item
from boto.dynamodb2.fields import HashKey, RangeKey, AllIndex, IncludeIndex, KeysOnlyIndex
from boto.dynamodb2.types import NUMBER

from . import datastructs
from .settings import config

logger = logging.getLogger(__name__)

# `threading.local` for Dynamo connections created outside of flask. gross.
_non_flask_threadlocal = threading.local()

def _make_dynamo_aws():
    """makes a connection to dynamo, based on configuration. For internal use.

    :rtype: dynamo connection object

    """
    try:
        access_id = config.aws.AWS_ACCESS_KEY_ID
        secret = config.aws.AWS_SECRET_ACCESS_KEY
    except (KeyError, pymlconf.ConfigurationError):
        access_id = None
        secret = None
    return DynamoDBConnection(aws_access_key_id=access_id,
                              aws_secret_access_key=secret)

def _make_dynamo_mock():
    """makes a connection to mock server, based on configuration. For internal use.

    :rtype: dynamo connection object

    """
    # based on https://ddbmock.readthedocs.org/en/v0.4.1/pages/getting_started.html#run-as-regular-client-server
    host='localhost'
    port=4567
    endpoint = '{}:{}'.format(host, port)
    region = RegionInfo(name='mock', endpoint=endpoint)
    conn = DynamoDBConnection(aws_access_key_id="AXX", aws_secret_access_key="SEKRIT", region=region, port=port, is_secure=False)

    # patch the region_name so boto doesn't explode
    conn._auth_handler.region_name = "us-mock-1"
    return conn

if config.dynamo.engine == 'aws':
    _make_dynamo = _make_dynamo_aws
elif config.dynamo.engine == 'mock':
    _make_dynamo = _make_dynamo_mock
else:
    raise RuntimeError("Bad value {} for config.dynamo.engine".format(config.dynamo.engine))

logger.debug("Installed engine %s", config.dynamo.engine)

def get_dynamo():
    """return a dynamo connection for this thread.

    All calls from the same thread return the same connection object. Do not save these or pass them around (esp. b/w threads!).
    """
    # largely copied from similar code in database.py
    try:
        dynamo = flask.g.dynamo
    except RuntimeError as err:
        # xxx gross, le sigh
        if err.message != "working outside of request context":
            raise
        else:
            # we are in a random thread the code spawned off from
            # $DIETY knows where. Here, have a connection:
            logger.debug("You made a Dynamo connection from random thread %d, and should feel bad about it.", threading.current_thread().ident)
            try:
                return _non_flask_threadlocal.dynamo
            except AttributeError:
                dynamo = _non_flask_threadlocal.dynamo = _make_dynamo()
    except AttributeError:
        # we are in flask-managed thread, which is nice.
        # create a new connection & save it for reuse
        dynamo = flask.g.dynamo= _make_dynamo()

    return dynamo

def _table_name(name):
    """return a table name using the prefix specified in config.

    For internal use.
    """
    return ".".join((config.dynamo.prefix, name))

def get_table(name):
    """Return a boto table for the given name

    :rtype: `boto.dynamodb2.table.Table`
    """
    # xxx might be desirable to cache these objects like in get_dynamo()
    table = Table(_table_name(name), connection=get_dynamo())
    table.describe()
    return table

def datetime_to_epoch(dt):
    """given a datetime, return seconds since the epoch"""
    return time.mktime(dt.utctimetuple())

def epoch_to_datetime(epoch):
    """given seconds since the epoch, return a datetime"""
    return datetime.datetime.fromtimestamp(epoch)

def date_to_epoch(d):
    """given a date, return seconds since the epoch"""
    return time.mktime(d.timetuple())

def epoch_to_date(epoch):
    """given seconds since the epoch, return a date"""
    return datetime.date.fromtimestamp(epoch)

def epoch_now():
    """return the current UTC time as seconds since the epoch"""
    return time.mktime(time.gmtime())

def remove_none_values(d):
    """Modify a dict in place by deleting items having None for value"""
    for k, v in d.items():
        if v is None:
            del d[k]

def create_table(**schema):
    """create a new table in Dynamo

    :arg dict schema: keyword args for `boto.dynamodb2.Table.create`
    """
    name = _table_name(schema['table_name'])
    logger.info("Creating table %s", name)
    schema['table_name'] = name
    return Table.create(connection=get_dynamo(), **schema)

def create_all_tables():
    """Create all tables in Dynamo.

    You should only call this method once.
    """
    dynamo = get_dynamo()
    create_table(**users_schema)
    create_table(**tokens_schema)
    create_table(**edges_incoming_schema)
    create_table(**edges_outgoing_schema)

def drop_all_tables():
    """Delete all tables in Dynamo"""
    for t in ('users', 'tokens', 'edges_outgoing', 'edges_incoming'):
        try:
            get_table(t).delete()
        except StandardError as e:
            logger.warn("Error deleting table %s: %s", t, e)
        else:
            logger.debug("Deleted table %s", t)

##### USERS #####

users_schema = {
    'table_name': 'users',
    'schema': [
        HashKey('fbid', data_type=NUMBER),
        ],
    'indexes': [],
}


def save_user(fbid, fname, lname, email, gender, birthday, city, state):
    """save a user to Dynamo. If user exists, update with new, non-None attrs.

    :arg int fbid: the user's facebook id

    Other args are string or None
    """

    updated = epoch_now()
    birthday = date_to_epoch(birthday) if birthday is not None else None

    data = locals()
    remove_none_values(data)

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

def fetch_user(fbid):
    """Fetch a user. Returns None if user not found.

    :arg str fbid: the users' Facebook ID
    :rtype: `datastructs.UserInfo`
    """
    table = get_table('users')
    x = table.get_item(fbid=fbid)
    if x['fbid'] is None: return None

    return _make_user(x)

def fetch_many_users(fbids):
    """Retrieve many users.

    :arg ids: list of facebook ID's
    :rtype: iterator of `datastructs.UserInfo`
    """
    table = get_table('users')
    results = table.batch_get(keys=[{'fbid': i} for i in fbids])
    users = (_make_user(x) for x in results if x['fbid'] is not None)
    return users

def _make_user(x):
    """make a `datastructs.UserInfo` from a boto Item. for internal use"""
    u = datastructs.UserInfo(uid=int(x['fbid']),
                             first_name=x['fname'],
                             last_name=x['lname'],
                             email=x['email'],
                             sex=x['gender'], # XXX aaah!
                             birthday=epoch_to_date(x['birthday']) if x['birthday'] is not None else None,
                             city=x['city'],
                             state=x['state'])

    # just stuff updated on there as an attr b/c we got nowhere else to put
    # it & we don't want to change fragile constructor above. :-|
    u.updated = epoch_to_datetime(x['updated'])
    return u

##### TOKENS #####

tokens_schema = {
    'table_name': 'tokens',
    'schema': [
        HashKey('fbid', data_type=NUMBER),
        RangeKey('appid', data_type=NUMBER)
    ]
}

def save_token(fbid, appid, token, expires):
    """save a token to dynamo, overwriting.

    :arg int fbid: the facebook id
    :arg int appid: the app's id
    :arg str token: the auth token from facebook
    :arg datetime expires: when the token expires, in GMT
    """
    table = get_table('tokens')
    x = Item(table, data = dict(
        fbid = fbid,
        appid = appid,
        token = token,
        expires = datetime_to_epoch(expires),
        updated = epoch_now()
        ))

    return x.save(overwrite=True)

def fetch_token(fbid, appid):
    """retrieve a token from facebook

    :arg int fbid: the facebook id
    :arg int appid: the app's id
    :rtype: `datastructs.TokenInfo` or None if not found
    """
    table = get_table('tokens')
    results = table.query(fbid__eq=fbid, appid__eq=appid)
    if not results:
        return None

    x = results.next()
    return datastructs.TokenInfo(tok = x['token'],
                                 own = int(x['fbid']),
                                 app = int(x['appid']),
                                 expires=epoch_to_datetime(x['expires']))

##### EDGES #####

edges_outgoing_schema = {
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

edges_incoming_schema = {
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


def save_edge(fbid_source, fbid_target, post_likes, post_comms, stat_likes, stat_comms, wall_posts, wall_comms, tags, photos_target, photos_other, mut_friends):
    """save an edge to dynamo

    :arg int fbid_source: the source's -> facebook id
    :arg int fbid_target: the -> target's facebook id

    Other args int or None
    """
    updated = epoch_now()

    data = locals()
    remove_none_values(data)

    # write to both tables
    for t in ('edges_incoming', 'edges_outgoing'):
        table = get_table(t)
        results = table.query(fbid_source__eq=fbid_source, fbid_target__eq=fbid_target)
        try:
            edge = results.next()
        except StopIteration:
            # new edge
            logger.debug("Saving new edge %s -> %s to table %s", fbid_source, fbid_target, t)
            table.put_item(data)
        else:
            # update existing edge. Don't even touch keys (which are
            # unchanged) because AWS/boto freak out
            logger.debug("Updating edge %s -> %s in table %s", fbid_source, fbid_target, t)
            for k, v in data.iteritems():
                if k not in ('fbid_source', 'fbid_target'):
                    edge[k] = v
            edge.partial_save()

def fetch_edge(fbid_source, fbid_target):
    """retrieve an edge from facebook

    :arg int fbid_source: the source's -> facebook id
    :arg int fbid_target: the -> target's facebook id
    :rtype: `datastructs.EdgeCount` or None if not found
    """
    # which table we retrieve off is arbitrary
    table = get_table('edges_incoming')
    results = table.query(fbid_source__eq = fbid_source, fbid_target__eq = fbid_target)
    try:
        e = results.next()
    except StopIteration:
        return None
    else:
        return _make_edge(e)

def fetch_all_incoming_edges():
    """Retrieve all incoming edges from dynamo

    WARNING: this does a full scan and is SLOW & EXPENSIVE

    :rtype: iter of `datastructs.EdgeCounts`
    """
    return imap(_make_edge, get_table('edges_incoming').scan())

def fetch_all_outgoing_edges():
    """Retrieve all outgoing edges from dynamo

    WARNING: this does a full scan and is SLOW & EXPENSIVE

    :rtype: iter of `datastructs.EdgeCounts`
    """
    return imap(_make_edge, get_table('edges_outgoing').scan())


def fetch_incoming_edges(fbid, newer_than=None):
    """Fetch many incoming edges

    select all edges where target == $fbid
    (and optionally) where updated > now() - $newer_than


    :arg int fbid: target facebook id
    :arg `datetime.datetime` newer_than: only include edges newer than this
    :rtype: iter of `datastructs.EdgeCounts`
    """
    table = get_table('edges_incoming')
    if newer_than is None:
        results = table.query(fbid_target__eq = fbid)
        return imap(_make_edge, results)
    else:
        keys = table.query(index = 'updated',
                           fbid_target__eq = fbid,
                           updated__gt = datetime_to_epoch(newer_than))
        return (fetch_edge(k['fbid_source'], k['fbid_target']) for k in keys)

def fetch_outgoing_edges(fbid, newer_than=None):
    """Fetch many outgoing edges

    select all edges where source == $fbid
    (and optionally) where updated > now() - $newer_than

    :arg int fbid: source facebook id
    :arg `datetime.datetime` newer_than: only include edges newer than this
    :rtype: iter of `datastructs.EdgeCounts`
    """
    table = get_table('edges_outgoing')
    if newer_than is None:
        results = table.query(fbid_source__eq = fbid)
        return imap(_make_edge, results)
    else:
        keys = table.query(index = 'updated',
                           fbid_source__eq = fbid,
                           updated__gt = datetime_to_epoch(newer_than))
        return (fetch_edge(k['fbid_source'], k['fbid_target']) for k in keys)

# internal helper to convert from dynamo's decimal
_int_or_none = lambda x: int(x) if x is not None else None

def _make_edge(x):
    """make an `datastructs.EdgeCount` from a boto Item. for internal use"""
    return datastructs.EdgeCounts(
        sourceId = int(x['fbid_source']),
        targetId = int(x['fbid_target']),
        postLikes = _int_or_none(x['post_likes']),
        postComms = _int_or_none(x['post_comms']),
        statLikes = _int_or_none(x['stat_likes']),
        statComms = _int_or_none(x['stat_comms']),
        wallPosts = _int_or_none(x['wall_posts']),
        wallComms = _int_or_none(x['wall_comms']),
        tags = _int_or_none(x['tags']),
        photoTarg = _int_or_none(x['photos_target']),
        photoOth = _int_or_none(x['photos_other']),
        muts = _int_or_none(x['mut_friends'])
        )