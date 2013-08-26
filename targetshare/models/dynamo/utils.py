from __future__ import print_function
import logging
import time
from StringIO import StringIO

from django.conf import settings


LOG = logging.getLogger(__name__)


class DummyIO(StringIO):

    def write(self, _buffer):
        pass

    def flush(self):
        pass


def _confirm(message):
    response = None
    while response not in ('', 'y', 'yes', 'n', 'no'):
        response = raw_input(message + " [Y|n]? ").strip().lower()
    return response in ('', 'y', 'yes')


class DynamoDB(object):

    def __init__(self, tables=None):
        self.tables = tables or set()

    @property
    def table_names(self):
        return {table.table_name.split('.', 1)[1]: table for table in self.tables}

    def register_item(self, sender, **_kws):
        """Register a Table, as an `item_declared` signal receiver."""
        self.tables.add(sender.items.table)

    @staticmethod
    def create_table(table):
        LOG.info("Creating table %s", table.table_name)
        return table.create(
            table_name=table.table_name,
            schema=table.schema,
            throughput=table.throughput,
            indexes=table.indexes,
            connection=table.connection,
        )

    def create_all_tables(self, timeout=0, wait=2, console=DummyIO()):
        """Create all tables in Dynamo.

        Table creation commands cannot be issued for two tables with secondary keys at
        once, and so commands are issued in order, and job status polled, to finish as
        quickly as possible without error.

        You should only have to call this method once.

        """
        if timeout < 0:
            raise ValueError("Invalid creation timeout")

        # Sort tables so as to create those with secondary keys last:
        tables = sorted(self.tables, key=lambda table: len(table.schema))

        for table_number, table_defn in enumerate(tables, 1):
            # Issue creation directive to AWS:
            table = self.create_table(table_defn)

            # Monitor job status:
            console.write("Table '{}' status: ".format(table.table_name))
            count = 0
            while count <= timeout:
                # Retrieve status:
                description = table.describe()
                status = description['Table']['TableStatus']

                # Update console:
                if count > 0:
                    console.write(".")
                if count == 0 or status != 'CREATING':
                    console.write(status)
                elif count >= timeout:
                    console.write("TIMEOUT")
                console.flush()

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

            print('', file=console) # Break line

    def drop_all_tables(self, confirm=False):
        """Delete all tables in Dynamo"""
        if confirm:
            continue_ = _confirm(
                "Drop tables [{tables}] with prefix '{prefix}' from dynamo"
                .format(
                    tables=', '.join(self.table_names),
                    prefix=settings.DYNAMO.prefix,
                )
            )
            if not continue_:
                return False

        for table in self.tables:
            try:
                table.delete()
            except StandardError:
                LOG.warn("Error deleting table %s", table.table_name, exc_info=True)
            else:
                LOG.debug("Deleted table %s", table.table_name)

        return True

    def truncate_all_tables(self):
        if not _confirm(
            "Truncate all data from tables [{tables}] with prefix '{prefix}'"
            .format(
                tables=', '.join(self.table_names),
                prefix=settings.DYNAMO.prefix,
            )
        ):
            return

        for table in self.tables:
            with table.batch_write() as batch:
                for item in table.scan():
                    batch.delete_item(**item.get_keys())

database = DynamoDB()