from mock import patch
from nose import tools

from targetshare.models.dynamo import base

from . import FaradayTestCase


class TestPrefetch(FaradayTestCase):

    User, Token = (None,) * 2

    @classmethod
    def setup_class(cls):
        class User(base.Item):
            uid = base.HashKeyField(data_type=base.NUMBER)

        class Token(base.Item):
            uid = base.HashKeyField(data_type=base.NUMBER)
            token = base.RangeKeyField()
            user = base.ItemLinkField(User, db_key=uid)

        cls.User = User
        cls.Token = Token

        cls.create_item_table(User, Token)

    def setup(self):
        self.user = self.User(uid=123)
        self.user.save()
        self.tokens = [self.Token(token=token_token) for token_token in ('abc', 'xyz')]
        for token in self.tokens:
            token.user = self.user
            token.save()

    def teardown(self):
        self.user.delete()
        for token in self.tokens:
            token.delete()

    def test_prefetch_parent_link(self):
        for token in self.user.tokens.all():
            tools.assert_true(vars(token).get('_user_cache'))
            get_item = self.User.items.table.get_item
            with patch.object(self.User.items.table, 'get_item') as mock_get_item:
                mock_get_item.side_effect = get_item
                user = token.user
            tools.assert_false(mock_get_item.called)
            tools.eq_(user, self.user)

    def test_prefetch_named_linked(self):
        for token in self.Token.items.prefetch('user').scan():
            tools.assert_true(vars(token).get('_user_cache'))
            get_item = self.User.items.table.get_item
            with patch.object(self.User.items.table, 'get_item') as mock_get_item:
                mock_get_item.side_effect = get_item
                user = token.user
            tools.assert_false(mock_get_item.called)
            tools.eq_(user, self.user)
