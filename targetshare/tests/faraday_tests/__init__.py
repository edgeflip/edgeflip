from boto.regioninfo import RegionInfo
from boto.dynamodb2.layer1 import DynamoDBConnection


def get_connection():
    host = 'localhost'
    port = 4444
    endpoint = '{}:{}'.format(host, port)
    region = RegionInfo(name='mock', endpoint=endpoint)
    conn = DynamoDBConnection(aws_access_key_id="AXX",
                              aws_secret_access_key="SEKRIT",
                              region=region,
                              port=port,
                              is_secure=False)
    # patch the region_name so boto doesn't explode
    conn._auth_handler.region_name = "us-mock-1"
    return conn


class FaradayTestCase(object):

    def setup(self):
        self.connection = get_connection()
        self.item_tables = []

    def teardown(self):
        for item in tuple(self.item_tables):
            item.items.table.delete()
            self.item_tables.remove(item)

    # TODO: Use item_declared signal to make this seamless?
    def create_item_table(self, *items):
        if not items:
            return

        item = items[0]
        table = item.items.table
        # Create table
        # (overwrite existing reference just to override default connection)
        item.items.table = table.create(
            table_name=table.table_name,
            item=table.item,
            schema=table.schema,
            throughput=table.throughput,
            indexes=table.indexes,
            connection=self.connection,
        )
        self.item_tables.append(item)
        self.create_item_table(*items[1:])
