"""Extension to the boto Table.

Models definition and interactions with a table in DynamoDB.

"""
import re

from boto.dynamodb2 import table, items
from django.conf import settings

from targetshare import utils

from . import db
from .results import BatchGetResultSet


# Subclass boto's Table & BatchTable to convert ResultSets and Items to ours #

inherits_docs = utils.doc_inheritor(table.BatchTable)


class BatchTable(table.BatchTable):

    @inherits_docs
    def put_item(self, data=None, overwrite=False, **kwdata):
        data = {} if data is None else data
        if kwdata:
            data = data if hasattr(data, 'update') else dict(data)
            data.update(kwdata)

        super(BatchTable, self).put_item(data, overwrite)

    @inherits_docs
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
            # %% done %%

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

        resp = self.table.connection.batch_write_item(batch_data)
        self.handle_unprocessed(resp)

        self._to_put = []
        self._to_delete = []
        return True


inherits_docs = utils.doc_inheritor(table.Table)


def get_short_name(table_name):
    return re.sub(r'^{}\.'.format(settings.DYNAMO.prefix), '', table_name)


def get_full_name(table_name):
    short_name = get_short_name(table_name)
    return '.'.join(part for part in (settings.DYNAMO.prefix, short_name) if part)


class Table(table.Table):
    """Extension to the boto Table.

    Models definition and interactions with a table in DynamoDB.

    """
    # create attempts to construct (otherwise without item):
    @classmethod
    def create(cls, table_name, item, # Add "item" to inherited interface
                 schema=None, throughput=None, indexes=None, connection=None):
        connection = connection or db.connection
        base = table.Table.create(
            get_full_name(table_name), schema, throughput, indexes, connection)
        return cls(base.table_name, item, base.schema, base.throughput,
                   base.indexes, base.connection)

    def __init__(self, table_name, item, # Add "item" to inherited interface
                 schema=None, throughput=None, indexes=None, connection=None):
        # Default to global (thread-local) connection:
        connection = connection or db.connection
        super(Table, self).__init__(table_name, schema, throughput, indexes, connection)
        self.item = item
        self._dynamizer = self.item.get_dynamizer()

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.table_name)

    # Bake (dynamic) dynamo prefix setting into table name -- misdirection, but means
    # we needn't manage prefix here.

    @property
    def short_name(self):
        return vars(self)['table_name']

    @property
    def table_name(self):
        return get_full_name(self.short_name)

    @table_name.setter
    def table_name(self, value):
        vars(self)['table_name'] = get_short_name(value)

    # Wrap returned ResultSets in friendlier LazySequences #

    @inherits_docs
    def query(self, *args, **kws):
        return utils.LazySequence(super(Table, self).query(*args, **kws))

    @inherits_docs
    def scan(self, *args, **kws):
        return utils.LazySequence(super(Table, self).scan(*args, **kws))

    # ...and use our BatchGetResultSet rather than boto's #

    @inherits_docs
    def batch_get(self, keys, *args, **kws):
        if not keys:
            # boto will pass empty list on to AWS, which responds with an error
            return utils.LazySequence()
        result = super(Table, self).batch_get(keys, *args, **kws)
        patched_result = BatchGetResultSet.clone(result)
        return utils.LazySequence(patched_result)

    # Use our Item rather than boto's #

    @inherits_docs
    def batch_write(self):
        return BatchTable(self)

    @inherits_docs
    def get_item(self, *args, **kws):
        item = super(Table, self).get_item(*args, **kws)
        # boto's get_item returns an empty Item if it doesn't exist.
        # Let's raise an exception instead:
        if not item.items():
            raise self.item.DoesNotExist
        return self.item(item, loaded=True)

    @inherits_docs
    def new_item(self, *args):
        item = super(Table, self).new_item(*args)
        return self.item(item)

    @inherits_docs
    def put_item(self, data=None, overwrite=False, **kwdata):
        item = self.item(data, **kwdata)
        return item.save(overwrite=overwrite)

    @inherits_docs
    def _batch_get(self, *args, **kws):
        result = super(Table, self)._batch_get(*args, **kws)
        result['results'] = [self.item(item, loaded=True)
                             for item in result['results']]
        return result

    @inherits_docs
    def _query(self, *args, **kws):
        result = super(Table, self)._query(*args, **kws)
        result['results'] = [self.item(item, loaded=True)
                             for item in result['results']]
        return result

    @inherits_docs
    def _scan(self, *args, **kws):
        result = super(Table, self)._scan(*args, **kws)
        result['results'] = [self.item(item, loaded=True)
                             for item in result['results']]
        return result
