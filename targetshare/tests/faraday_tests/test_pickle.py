import pickle

from nose import tools

from targetshare.models.dynamo import base

from . import FaradayTestCase


class User(base.Item):
    uid = base.HashKeyField(data_type=base.NUMBER)


class Token(base.Item):
    uid = base.HashKeyField(data_type=base.NUMBER)
    token = base.RangeKeyField()
    user = base.ItemLinkField(User, db_key=uid)


class TestPickling(FaradayTestCase):

    def setup(self):
        super(TestPickling, self).setup()
        self.create_item_table(User, Token)

    def test_pickle(self):
        pickle.dumps(Token(uid=123, token='abc'), 2)

    def test_pickle_linked_manager(self):
        user = User(uid=123)
        tools.assert_true(user.tokens)
        pickle.dumps(user, 2)
