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

    return Table(_table_name(name), connection=get_dynamo())

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


def save_user(fbid, fname, lname, email, gender, birthday, city, state, partial=True):
    table = get_table('users')
    u = Item(table, data = dict(
        fbid = fbid,
        fname = fname,
        lname = lname,
        email = email,
        gender = gender,
        city = city,
        state = state,
        birthday = date_to_epoch(birthday),
        updated = epoch_now()
        ))

    if partial:
        u.partial_save()
    else:
        u.save()

def fetch_user(fbid):
    table = get_table('users')
    u = table.get_item(fbid=fbid)
    return datastructs.UserInfo(uid=u['fbid'],
                                first_name=u.get('fname'),
                                last_name=u.get('lname'),
                                email=u.get('email'),
                                sex=u.get('sex'),
                                birthday=epoch_to_date(u['birthday']) if 'birthday' in u else None,
                                city=u.get('city'),
                                state=u.get('state'),
                                updated=epoch_to_datetime(u['updated']))

