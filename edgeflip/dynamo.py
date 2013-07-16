#!/usr/bin/env python
"""
tools & classes for data stored in AWS DynamoDB


.. envvar:: dynamo.prefix

    String prefix to prepend to table names. A `.` is used as a separtor

.. envvar:: dynamo.engine

    Which engine to use. One of 'aws', 'mock'.

"""
import logging
import threading
import flask
import pymlconf
import time
import datetime

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

    :rtype: mysql connection object

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

    :rtype: mysql connection object

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
    """return a connection for this thread.

    All calls from the same thread return the same connection object. Do not save these or pass them around (esp. b/w threads!).
    """
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
    create_table(**edges_data_schema)
    create_table(**edges_incoming_schema)

def drop_all_tables():
    """Delete all tables in Dynamo"""
    for t in ('users', 'tokens', 'edges_data', 'edges_incoming'):
        get_table(t).delete()

##### USERS #####

users_schema = {
    'table_name': 'users',
    'schema': [
        HashKey('fbid', data_type=NUMBER),
        ],
    'indexes': [],
}


def save_user(fbid, fname, lname, email, gender, birthday, city, state):
    updated = epoch_now()
    birthday = date_to_epoch(birthday) if birthday is not None else None

    data = locals()
    remove_none_values(data)

    table = get_table('users')
    user = table.get_item(fbid=fbid)

    for k, v in data.iteritems():
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
    """
    table = get_table('edges')
    results = table.batch_get([{'fbid': i} for i in fbids])
    return [_make_user(x) for x in results if x['fbid'] is not None]

def _make_user(x):
    """make a user from a boto Item. for internal use"""
    return datastructs.UserInfo(id=x['fbid'],
                                first_name=x['fname'],
                                last_name=x['lname'],
                                email=x['email'],
                                sex=x['gender'], # XXX aaah!
                                birthday=epoch_to_date(x['birthday']) if x['birthday'] is not None else None,
                                city=x['city'],
                                state=x['state'],
                                updated=epoch_to_datetime(x['updated']))

##### TOKENS #####

tokens_schema = {
    'table_name': 'tokens',
    'schema': [
        HashKey('fbid', data_type=NUMBER),
        RangeKey('appid', data_type=NUMBER)
    ]
}

def save_token(fbid, appid, token, expires):
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
    table = get_table('tokens')
    x = table.get_item(fbid, appid)
    if x['fbid_appid'] is None: return None

    return datastructs.TokenInfo(tok = x['token'],
                                 own = x['fbid'],
                                 app = x['appid'],
                                 expires=epoch_to_datetime(x['expires']))

##### EDGES #####

edges_data_schema = {
    'table_name': 'edges_data',
    'schema': [
        HashKey('fbid_source', data_type=NUMBER),
        RangeKey('fbid_target', data_type=NUMBER)
        ],
    'indexes': [
        IncludeIndex('edges_outgoing',
                     parts=[HashKey('fbid_source', data_type=NUMBER),
                            RangeKey('updated', data_type=NUMBER)],
                     includes=['fbid_source', 'fbid_target']),
    ]
}

edges_incoming_schema = {
    'table_name': 'edges_incoming',
        'schema': [
            HashKey('fbid_target', data_type=NUMBER),
            RangeKey('updated', data_type=NUMBER)
            # fbid_source is saved as a field            
            ],        
}

def save_edge(fbid_source, fbid_target, post_likes, post_comms, stat_likes, stat_comms, wall_posts, wall_comms, tags, photos_target, photos_other, mut_friends):
    updated = epoch_now()

    data = locals()
    remove_none_values(data)

    table = get_table('edges_data')
    edge = table.get_item(fbid_source, fbid_target)

    for k, v in data.iteritems():
        edge[k] = v

    return edge.partial_save()

def fetch_edge(fbid_source, fbid_target):
    table = get_table('edges_data')
    x = table.get_item(fbid_source, fbid_target)
    if x['source_target'] is None: return None
    return _make_edge(x)


def fetch_many_edges(ids):
    """Retrieve many edges.

    :arg ids: list of 2-tuples of (fbid_source, fbid_target)
    """
    table = get_table('edges_data')
    results = table.batch_get([{'fbid_source':s, 'fbid_target':t} for s, t in ids])
    return [_make_edge(x) for x in results if x['source_target'] is not None]

def fetch_incoming_edges(fbid, newer_than=None):
    """Fetch many edges from secondary -> primary

    :arg str fbid: primary's facebook id
    :arg `datetime.datetime` newer_than: only include edges newer than this
    :rtype: list of `datastructs.EdgeCounts`
    """
    table = get_table('edges_incoming')
    if newer_than is None:
        results = table.query(fbid_target = fbid)
    else:
        keys = table.query(index = 'edges_incoming', fbid_target = fbid, updated__gt = datetime_to_epoch(newer_than))
        results = fetch_many_edges((k['fbid_source'], k['fbid_target']) for k in keys)
    return map(_make_edge, results)

def fetch_outgoing_edges(fbid, newer_than=None):
    """Fetch many edges from primary -> secondary

    :arg str fbid: primary's facebook id
    :arg `datetime.datetime` newer_than: only include edges newer than this
    :rtype: list of `datastructs.EdgeCounts`
    """
    table = get_table('edges_data')
    if newer_than is None:
        results = table.query(fbid_source = fbid)
    else:
        keys = table.query(index = 'edges_outgoing',
                           fbid_source = fbid,
                           updated__gt = datetime_to_epoch(newer_than),
                           attributes_to_get = ['fbid_source', 'fbid_target'])
        results = fetch_many_edges((k['fbid_source'], k['fbid_target']) for k in keys) 
    return map(_make_edge, results)

def _make_edge(x):
    """make an edge from a boto Item. for internal use"""
    return datastructs.EdgeCounts(
        sourceId = x['fbid_source'],
        targetId = x['fbid_target'],
        postLikes = x['post_likes'],
        postComms = x['post_comms'],
        statLikes = x['stat_likes'],
        statComms = x['stat_comms'],
        wallPosts = x['wall_posts'],
        wallComms = x['wall_comms'],
        tags = x['tags'],
        photoTarg = x['photos_target'],
        photoOth = x['photos_other'],
        muts = x['mut_friends']
        )