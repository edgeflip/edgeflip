from nose import tools

from targetshare.models import datastructs


class TestShortToken(object):

    def setup(self):
        self.token = datastructs.ShortToken(fbid=1, appid='123', token='1Z0A', api='1.0')

    def test_as_tuple(self):
        tools.eq_(self.token, (1, '123', '1Z0A', '1.0'))

    def test_as_object(self):
        tools.eq_(self.token.fbid, 1)
        tools.eq_(self.token.appid, '123')
        tools.eq_(self.token.token, '1Z0A')
        tools.eq_(self.token.api, '1.0')

    @tools.raises(AttributeError)
    def test_no_save(self):
        self.token.save()
