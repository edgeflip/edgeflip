#!/usr/bin/env python
"""
tools & classes for data stored in AWS DynamoDB


.. envvar:: dynamo.prefix

    String prefix to prepend to table names. A `.` is used as a separtor

"""

import logging
import threading
import flask
import pymlconf
import time
import datetime


from boto import connect_dynamodb
from boto.dynamodb2.table import Table
from boto.dynamodb2.items import Item
from boto.dynamodb2.fields import HashKey, AllIndex, IncludeIndex
from boto.dynamodb2.types import NUMBER, STRING

from . import datastructs
from .settings import config

logger = logging.getLogger(__name__)

# `threading.local` for Dynamo connections created outside of flask. gross.
_non_flask_threadlocal = threading.local()

def _make_dynamo():
    """makes a connection to dynamo, based on configuration. For internal use.

    :rtype: mysql connection object

    """
    try:
        access_id = config.aws.AWS_ACCESS_KEY_ID
        secret = config.aws.AWS_SECRET_ACCESS_KEY
    except (KeyError, pymlconf.ConfigurationError):
        access_id = None
        secret = None
    return connect_dynamodb(access_id, secret)

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
    return time.mktime(d.timetuple)

def epoch_to_date(epoch):
    """given seconds since the epoch, return a date"""
    return datetime.date.fromtimestamp(epoch)

def epoch_now():
    """return the current UTC time as seconds since the epoch"""
    return time.mktime(time.gmtime())

def remove_none_values(d):
    """Modify a dict in place by deleting items having None for value"""
    for k, v in d.iteritems():
        if v is None:
            del d[k]

def create_table(**schema):
    """create a new table in Dynamo

    :arg dict schema: keyword args for `boto.dynamodb2.Table.create`
    """
    schema['table_name'] = _table_name['table_name']
    return Table.create(connection=get_dynamo(), **schema)

users_schema = {
    'table_name': 'users',
    'schema': [
        HashKey('fbid', data_type=STRING),
        ],
    'indexes': None,
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

    user.partial_save()

def fetch_user(fbid):
    table = get_table('users')
    x = table.get_item(fbid=fbid)
    if x['fbid'] is None: return None

    return datastructs.UserInfo(uid=x['fbid'],
                                first_name=x['fname'],
                                last_name=x['lname'],
                                email=x['email'],
                                sex=x['sex'],
                                birthday=epoch_to_date(x['birthday']) if x['birthday'] is not None else None,
                                city=x['city'],
                                state=x['state'],
                                updated=epoch_to_datetime(x['updated']))

tokens_schema = {
    'table_name': 'tokens',
    'schema': [
        HashKey('fbid_appid', data_type=STRING),
        ],
    'indexes': None,
    }

def save_token(fbid, appid, token, expires):
    table = get_table('tokens')
    x = Item(table, data = dict(
        fbid_appid = ".".join((fbid, appid)),
        fbid = fbid,
        appid = appid,
        token = token,
        expires = datetime_to_epoch(expires),
        updated = epoch_now()
        ))

    x.save()

def fetch_token(fbid, appid):
    table = get_table('tokens')
    x = table.get_item(fbid_appid=".".join((fbid, appid)))
    if x['fbid_appid'] is None: return None

    return datastructs.TokenInfo(tok = x['token'],
                                 own = x['fbid'],
                                 app = x['appid'],
                                 expires=epoch_to_datetime(x['expires']))


edges_schema = {
    'table_name': 'edges',
    'schema': [
        HashKey('source_target', data_type=STRING),
        ],
    'indexes': None,
    }

def save_edge(fbid_source, fbid_target, post_likes, post_comms, stat_likes, stat_comms, wall_posts, wall_comms, tags, photos_target, photos_other, mut_friends):
    table = get_table('edges')
    x = Item(table, data = dict(
        source_target = ".".join((fbid_source, fbid_target)),
        fbid_source = fbid_source,
        fbid_target = fbid_target,
        post_likes = post_likes,
        post_comms = post_comms,
        stat_likes = stat_likes,
        stat_comms = stat_comms,
        wall_posts = wall_posts,
        wall_comms = wall_comms,
        tags = tags,
        photos_target = photos_target,
        photos_other = photos_other,
        mut_friends = mut_friends,
        updated = epoch_now()
        ))

    x.save()

def fetch_edge(fbid_source, fbid_target):
    table = get_table('edges')
    x = table.get_item(source_target=".".join((fbid_source, fbid_target)))
    if x['source_target'] is None: return None

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