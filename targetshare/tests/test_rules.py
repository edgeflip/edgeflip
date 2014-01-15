from nose import tools

from targetshare.utils.rule import context, RuleSet, BoundDecision, Decision


class RuleSetTestCase(object):

    def setup(self):

        class WearPants(RuleSet):

            WEAR_PANTS = Decision()
            NO_PANTS = Decision()

            def __init__(self, cold=False):
                self.cold = cold

            @RuleSet.rule
            def its_cold(self):
                if self.cold:
                    return self.WEAR_PANTS

            @RuleSet.rule
            def whatever(self):
                return self.NO_PANTS

        self.rule_set = WearPants


class TestRuleSet(RuleSetTestCase):

    def test_defn(self):
        tools.eq_(self.rule_set.decisions,
                  {self.rule_set.WEAR_PANTS, self.rule_set.NO_PANTS})
        tools.eq_(self.rule_set.rules,
                  [self.rule_set.its_cold, self.rule_set.whatever])

        naive_decision = self.rule_set(True).its_cold()
        tools.eq_(naive_decision, self.rule_set.WEAR_PANTS)
        tools.eq_(self.rule_set.WEAR_PANTS.owner, self.rule_set)

    def test_decision(self):
        decision = self.rule_set().decide()
        tools.assert_is_instance(decision, BoundDecision)
        tools.eq_(decision.made_by, self.rule_set.whatever)

    def test_decision_1(self):
        tools.eq_(self.rule_set().decide(), self.rule_set.NO_PANTS)

    def test_apply_decision_1(self):
        tools.eq_(self.rule_set.apply(), self.rule_set.NO_PANTS)

    def test_decision_2(self):
        tools.eq_(self.rule_set(True).decide(), self.rule_set.WEAR_PANTS)

    def test_apply_decision_2(self):
        tools.eq_(self.rule_set.apply(True), self.rule_set.WEAR_PANTS)


class TestRuleSetInheritance(RuleSetTestCase):

    def setup(self):
        super(TestRuleSetInheritance, self).setup()

        class WearPantsCommitted(self.rule_set):

            NEW_PANTS = Decision(color='blue')

            def __init__(self, cold=False, its_time=False):
                super(WearPantsCommitted, self).__init__(cold)
                self.its_time = its_time

            @RuleSet.rule
            def s_o(self):
                if self.its_time:
                    return self.NEW_PANTS

        self.child = WearPantsCommitted

    def test_defn(self):
        tools.eq_(self.child.decisions,
                  {self.child.WEAR_PANTS, self.child.NO_PANTS, self.child.NEW_PANTS})
        tools.assert_not_in(self.rule_set.NO_PANTS, self.child.decisions)
        tools.assert_not_equal(self.child.NO_PANTS, self.rule_set.NO_PANTS)
        tools.eq_(self.child.NO_PANTS.owner, self.child)
        tools.eq_(self.rule_set.NO_PANTS.owner, self.rule_set)

        tools.eq_(self.child.rules,
                  [self.child.its_cold, self.child.whatever, self.child.s_o])
        tools.eq_(self.child.its_cold.owners, {self.rule_set, self.child})

        naive_decision = self.child(its_time=True).s_o()
        tools.eq_(naive_decision, self.child.NEW_PANTS)
        tools.eq_(naive_decision.meta['color'], 'blue')


class TestFunctionalRules(object):

    def test_basic(self):

        @context
        def go_home(time):
            return {'time': time}

        @go_home.rule
        def its_late(context):
            return context.time > 18

        tools.eq_(go_home.rules, [its_late])
        tools.assert_false(go_home.decisions)

        tools.assert_true(go_home.apply(18.4))
        tools.assert_false(go_home.apply(14))

    def test_decisions(self):

        @context(GO_HOME=Decision())
        def go_home(time):
            return {'time': time}

        @go_home.rule
        def its_late(context):
            if context.time > 18:
                return context.GO_HOME

        tools.eq_(go_home.rules, [its_late])
        tools.eq_(go_home.decisions, {go_home.GO_HOME})

        tools.eq_(go_home.apply(18.4), go_home.GO_HOME)
        tools.assert_raises(go_home.IndecisionError, go_home.apply, 14)
