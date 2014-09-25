from nose import tools

from gerry.match import impute_feature


class User(object):

    def __init__(self, id=0, fname="Gerry", lname="App", city="Phila", state="PA"):
        self.id = id
        self.fname = fname
        self.lname = lname
        self.city = city
        self.state = state
        self.gotv_score = None
        self.persuasion_score = None


class GerryTestCase(object):

    pass


class TestUnsupportedFeature(object):

    def test(self):
        with tools.assert_raises(ValueError) as context:
            impute_feature(User(), 'gerry_score')
        tools.assert_in("Unsupported feature", str(context.exception))
