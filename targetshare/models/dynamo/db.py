"""The DynamoDB `connection`

.. envvar:: dynamo.prefix

    String prefix to prepend to table names. A `.` is used as a separtor

.. envvar:: dynamo.engine

    Which engine to use. One of 'aws', 'mock'.

"""
import threading
import pymlconf

from boto.regioninfo import RegionInfo
from boto.dynamodb2.layer1 import DynamoDBConnection
from django.conf import settings


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
