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

    connection = get_connection()
    created_items = {}

    @classmethod
    def teardown_class(cls):
        for item_name in cls.created_items.keys():
            item = cls.created_items.pop(item_name)
            table = item.items.table
            table.delete()

    @classmethod
    def create_item_table(cls, *items):
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
            connection=cls.connection,
        )
        cls.created_items[item.__name__] = item
        cls.create_item_table(*items[1:])
