"""Extension to the boto Table.

Models definition and interactions with a table in DynamoDB.

"""
from boto.dynamodb2 import table, items
from django.conf import settings

from targetshare.models.dynamo import db

from .results import BatchGetResultSet


# Subclass boto's Table & BatchTable to convert ResultSets and Items to ours #

class BatchTable(table.BatchTable):

    # boto's BatchTable.flush uses its Item right in the middle...
    # Copy of BatchTable's flush (except for %%):
    def flush(self):
        batch_data = {
            self.table.table_name: [
                # We'll insert data here shortly.
            ],
        }

        for put in self._to_put:
            # %% Allow for specification by Item, or use Table's Item,
            # rather than boto's:
            #item = Item(self.table, data=put)
            item = put if isinstance(put, items.Item) else self.table.item(put)

            batch_data[self.table.table_name].append({
                'PutRequest': {
                    'Item': item.prepare_full(),
                }
            })

        for delete in self._to_delete:
            batch_data[self.table.table_name].append({
                'DeleteRequest': {
                    'Key': self.table._encode_keys(delete),
                }
            })

        self.table.connection.batch_write_item(batch_data)
        self._to_put = []
        self._to_delete = []
        return True


class Table(table.Table):
    """Extension to the boto Table.

    Models definition and interactions with a table in DynamoDB.

    """
    def __init__(self, table_name, schema=None, throughput=None, indexes=None,
                 connection=None,
                 item=None): # Add "item" to inherited interface
        # Default to global (thread-local) connection:
        connection = connection or db.connection
        super(Table, self).__init__(table_name, schema, throughput, indexes, connection)
        self.item = item

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.table_name)

    @property
    def table_name(self):
        try:
            return vars(self)['table_name']
        except KeyError:
            raise AttributeError("'{}' object has no attribute 'table_name'"
                                 .format(self.__class__.__name__))

    @table_name.setter
    def table_name(self, table_name):
        """Allow table_name to be specified without global prefix."""
        if table_name.startswith(settings.DYNAMO.prefix):
            _prefix, short_name = table_name.split('.', 1)
        else:
            short_name = table_name
            table_name = '{}.{}'.format(settings.DYNAMO.prefix, table_name)
        vars(self).update(table_name=table_name, short_name=short_name)

    @property
    def short_name(self):
        try:
            return vars(self)['short_name']
        except KeyError:
            raise AttributeError("'{}' object has no attribute 'short_name'"
                                 .format(self.__class__.__name__))

    # Use our BatchGetResultSet rather than boto's #

    def batch_get(self, *args, **kws):
        result = super(Table, self).batch_get(*args, **kws)
        return BatchGetResultSet.from_boto(result)

    # Use our Item rather than boto's #

    def batch_write(self):
        return BatchTable(self)

    def get_item(self, *args, **kws):
        item = super(Table, self).get_item(*args, **kws)
        # boto's get_item returns an empty Item if it doesn't exist.
        # Let's raise an exception instead:
        if not item.items():
            raise self.item.DoesNotExist
        return self.item.from_boto(item)

    def put_item(self, data, overwrite=False):
        item = self.item(self, data=data)
        return item.save(overwrite=overwrite)

    def _batch_get(self, *args, **kws):
        result = super(Table, self)._batch_get(*args, **kws)
        result['results'] = [self.item.from_boto(item) for item in result['results']]
        return result

    def _query(self, *args, **kws):
        result = super(Table, self)._query(*args, **kws)
        result['results'] = [self.item.from_boto(item) for item in result['results']]
        return result

    def _scan(self, *args, **kws):
        result = super(Table, self)._scan(*args, **kws)
        result['results'] = [self.item.from_boto(item) for item in result['results']]
        return result
