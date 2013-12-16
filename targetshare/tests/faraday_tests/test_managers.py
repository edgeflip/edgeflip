from mock import patch
from nose import tools

from targetshare.models.dynamo import base

from . import FaradayTestCase


class TestPrefetch(FaradayTestCase):

    def setup(self):
        class User(base.Item):
            uid = base.HashKeyField(data_type=base.NUMBER)

        class Token(base.Item):
            uid = base.HashKeyField(data_type=base.NUMBER)
            token = base.RangeKeyField()
            user = base.ItemLinkField(User, db_key=uid)

        self.User = User
        self.Token = Token

        super(TestPrefetch, self).setup()
        self.create_item_table(self.User, self.Token)

        self.user = self.User(uid=123)
        self.user.save()
        self.tokens = [self.Token(token=token_token) for token_token in ('abc', 'xyz')]
        for token in self.tokens:
            token.user = self.user
            token.save()

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
