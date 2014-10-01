from decimal import Decimal

from nose import tools

from gerry import bulk_impute, impute_feature, models

from . import GerryTestCase


class User(object):

    def __init__(self, id=0, fname="Gerry", lname="App", city="Philadelphia", state="Pennsylvania"):
        self.id = id
        self.fname = fname
        self.lname = lname
        self.city = city
        self.state = state


class TestBulkImpute(GerryTestCase):

    def setUp(self):
        super(TestBulkImpute, self).setUp()
        self.user = User()

    def test_no_match(self):
        bulk_impute([self.user], 'gotv_score')
        tools.assert_is_none(self.user.gotv_score)

    def test_no_score(self):
        models.StateNameVoter.items.create(
            state_lname_fname="PA_APP_GERRY",
            persuasion_score='1.2',
        )
        bulk_impute([self.user], 'gotv_score')
        tools.assert_is_none(self.user.gotv_score)

    def test_no_state(self):
        self.user.state = None
        bulk_impute([self.user], 'gotv_score')
        tools.assert_is_none(self.user.gotv_score)

    def test_bad_state(self):
        self.user.state = 'garbage'
        bulk_impute([self.user], 'gotv_score')
        tools.assert_is_none(self.user.gotv_score)

    def test_same_signature_matches(self):
        models.StateNameVoter.items.create(
            state_lname_fname="PA_APP_GERRY",
            gotv_score='0.2',
            persuasion_score='1.2',
        )
        users = [User(id=id) for id in xrange(2)]
        bulk_impute(users, 'gotv_score')
        tools.eq_([user.gotv_score for user in users], [Decimal('0.2')] * 2)

    def test_fallback(self):
        models.StateNameVoter.items.create(
            state_lname_fname="PA_APP_GERRY",
            gotv_score='0.2',
            persuasion_score='1.2',
        )
        bulk_impute([self.user], 'gotv_score')
        tools.eq_(self.user.gotv_score, Decimal('0.2'))

    def test_priority(self):
        models.StateNameVoter.items.create(
            state_lname_fname="PA_APP_GERRY",
            gotv_score='0.2',
            persuasion_score='1.2',
        )
        models.StateCityNameVoter.items.create(
            state_city_lname_fname="PA_PHILADELPHIA_APP_GERRY",
            gotv_score='0.4',
            persuasion_score='4.2',
        )
        bulk_impute([self.user], 'gotv_score')
        tools.eq_(self.user.gotv_score, Decimal('0.4'))

    def test_unsupported_feature(self):
        with tools.assert_raises(ValueError) as context:
            bulk_impute([self.user], 'gerry_score')
        tools.assert_in("Unsupported feature", str(context.exception))


class TestImputeFeature(GerryTestCase):

    def test_unsupported_feature(self):
        with tools.assert_raises(ValueError) as context:
            impute_feature(User(), 'gerry_score')
        tools.assert_in("Unsupported feature", str(context.exception))
