import os
import time
import threading

from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError

from . import conf, loading, utils


### connection ###

def _make_dynamo_aws():
    """Make a connection to dynamo, based on configuration.

    For internal use.

    :rtype: dynamo connection object

    """
    access_id = getattr(conf.settings, 'AWS_ACCESS_KEY_ID', None)
    if not access_id:
        access_id = os.environ.get('AWS_ACCESS_KEY_ID')

    secret = getattr(conf.settings, 'AWS_SECRET_ACCESS_KEY', None)
    if not secret:
        secret = os.environ.get('AWS_SECRET_ACCESS_KEY')

    return DynamoDBConnection(aws_access_key_id=access_id,
                              aws_secret_access_key=secret)


def _make_dynamo_mock():
    """Make a connection to the mock dynamo server, based on configuration.

    For internal use.

    :rtype: dynamo connection object

    """
    # Based on: https://ddbmock.readthedocs.org/en/v0.4.1/pages/getting_started.html#run-as-regular-client-server
    endpoint = conf.settings.MOCK
    _host, port = endpoint.split(':')
    region = RegionInfo(name='mock', endpoint=endpoint)
    conn = DynamoDBConnection(
        aws_access_key_id="AXX",
        aws_secret_access_key="SEKRIT",
        region=region,
        port=port,
        is_secure=False,
    )
    # patch the region_name so boto doesn't explode:
    conn._auth_handler.region_name = "us-mock-1"
    return conn


def _make_dynamo():
    """Retrive a [mock] dynamo server connection, based on configuration.

    For internal use.

    """
    engine = conf.settings.engine

    if engine == 'aws':
        return _make_dynamo_aws()

    if engine == 'mock':
        return _make_dynamo_mock()

    raise conf.ConfigurationValueError("Bad value {!r} for ENGINE".format(engine))


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


### Management ###


def _tables():
    return (item.items.table for item in loading.cache)


def _named_tables():
    return (table.short_name for table in _tables())


def status():
    for table in _tables():
        description = table.describe()
        status = description['Table']['TableStatus']
        yield (table.table_name, status)


def create_table(table, throughput=None):
    return table.create(
        table_name=table.table_name,
        item=table.item,
        schema=table.schema,
        throughput=(throughput or table.throughput),
        indexes=table.indexes,
        connection=table.connection,
    )


def build(timeout=0, wait=2, stdout=utils.dummyio, throughput=None):
    """Create all tables in Dynamo.

    Table creation commands cannot be issued for two tables with secondary keys at
    once, and so commands are issued in order, and job status polled, to finish as
    quickly as possible without error.

    You should only have to call this method once.

    """
    if timeout < 0:
        raise ValueError("Invalid creation timeout")

    # Sort tables so as to create those with secondary keys last:
    tables = sorted(_tables(), key=lambda table: len(table.schema))

    for (table_number, table_defn) in enumerate(tables, 1):
        # Issue creation directive to DDB:
        try:
            table = create_table(table_defn, throughput)
        except JSONResponseError:
            utils.LOG.exception('Failed to create table %s', table_defn.table_name)
            continue

        # Monitor job status:
        stdout.write("Table '{}' status: ".format(table.table_name))
        count = 0
        while count <= timeout:
            # Retrieve status:
            description = table.describe()
            status = description['Table']['TableStatus']

            # Update console:
            if count > 0:
                stdout.write(".")

            if count == 0 or status != 'CREATING':
                stdout.write(status)
            elif count >= timeout:
                stdout.write("TIMEOUT")

            stdout.flush()

            if (
                status != 'CREATING' or        # Creation completed
                count >= timeout or            # We're out of time
                len(table.schema) == 1 or      # Still processing non-blocking tables
                table_number == len(tables)    # This is the last table anyway
            ):
                break # We're done, proceed

            if count + wait <= timeout:
                step = wait
            else:
                step = timeout - count
            time.sleep(step)
            count += step

        stdout.write('\n') # Break line


def _confirm(message):
    response = None
    while response not in ('', 'y', 'yes', 'n', 'no'):
        response = raw_input(message + " [Y|n]? ").strip().lower()
    return response in ('', 'y', 'yes')


def destroy(confirm=True):
    """Delete all tables in Dynamo"""
    if confirm and not _confirm(
        "Drop tables [{tables}]{prefix} from dynamo"
        .format(
            tables=', '.join(_named_tables),
            prefix=(" with prefix '{}'".format(conf.settings.PREFIX)
                    if conf.settings.PREFIX else ''),
        )
    ):
        return False

    for table in _tables():
        try:
            table.delete()
        except StandardError:
            utils.LOG.warn("Error deleting table %s", table.table_name, exc_info=True)
        else:
            utils.LOG.info("Deleted table %s", table.table_name)

    return True


def truncate(confirm=True):
    if confirm and not _confirm(
        "Truncate all data from tables [{tables}]{prefix}"
        .format(
            tables=', '.join(_named_tables),
            prefix=(" with prefix '{}'".format(conf.settings.PREFIX)
                    if conf.settings.PREFIX else ''),
        )
    ):
        return False

    for table in _tables():
        with table.batch_write() as batch:
            for item in table.scan():
                batch.delete_item(**item.get_keys())

    return True
