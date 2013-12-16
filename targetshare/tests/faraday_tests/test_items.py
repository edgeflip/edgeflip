from nose import tools

from targetshare.models.dynamo import base

from . import FaradayTestCase


class TestEquality(FaradayTestCase):

    class Token(base.Item):
        uid = base.HashKeyField(data_type=base.NUMBER)
        token = base.RangeKeyField()

    def setup(self):
        super(TestEquality, self).setup()
        self.create_item_table(self.Token)

    def test_eq(self):
        t0 = self.Token(uid=123, token='abc')
        t1 = self.Token(uid=123, token='abc')
        tools.assert_is_not(t0, t1)
        tools.assert_equal(t0, t1)
        tools.assert_equal(hash(t0), hash(t1))

    def test_ne(self):
        t0 = self.Token(uid=923, token='abc')
        t1 = self.Token(uid=123, token='abc')
        tools.assert_not_equal(t0, t1)
        tools.assert_not_equal(hash(t0), hash(t1))
