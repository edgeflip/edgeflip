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
import calendar
import logging
import threading
import pymlconf
import time
import types
import datetime
from itertools import imap

from boto.regioninfo import RegionInfo
from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.dynamodb2.table import Table
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


def table_name(name):
    """return a table name using the prefix specified in config.

    For internal use.
    """
    return ".".join((settings.DYNAMO.prefix, name))


def get_table(name):
    """Return a boto table for the given name

    :rtype: `boto.dynamodb2.table.Table`
    """
    return Table(table_name(name),
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


##### USERS #####

SCHEMAS['users'] = {
    'table_name': 'users',
    'schema': [
        HashKey('fbid', data_type=NUMBER),
    ],
    'indexes': [],
}


##### TOKENS #####

SCHEMAS['tokens'] = {
    'table_name': 'tokens',
    'schema': [
        HashKey('fbid', data_type=NUMBER),
        RangeKey('appid', data_type=NUMBER)
    ]
}


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
