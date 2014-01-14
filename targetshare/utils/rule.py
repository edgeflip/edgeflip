"""A framework for the definition and application of rule sets."""
import copy


class Rule(object):

    def __init__(self, func):
        self.func = func
        self.owners = set()

    @property
    def __name__(self):
        return self.func.__name__

    def __call__(self, context):
        return self.func(context)

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.func)

    def __str__(self):
        return self.__name__


class Decision(object):

    is_bound = False

    def __init__(self, name=None, **meta):
        self.name = name
        self.meta = meta
        self.owner = None

    def __hash__(self):
        return hash((self.owner, self.name))

    def bind(self, rule):
        return BoundDecision(name=self.name,
                             owner=self.owner,
                             made_by=rule,
                             **self.meta)


class BoundDecision(Decision):

    is_bound = True

    def __init__(self, name, owner, made_by, **meta):
        super(BoundDecision, self).__init__(name, **meta)
        self.owner = owner
        self.made_by = made_by


class RuleSetDefinition(type):

    def __new__(mcs, name, bases, dict_):
        # Initialize class attributes:
        for (name, default) in [
            ('decisions', set()),
            ('rules', []),
        ]:
            try:
                dict_[name]
            except KeyError:
                pass
            else:
                continue

            # Attempt to copy concrete ancestor's value:
            for base in bases:
                try:
                    inherited = getattr(base, name)
                except AttributeError:
                    pass
                else:
                    dict_[name] = copy.copy(inherited)
                    break
            else:
                dict_[name] = default

        return super(RuleSetDefinition, mcs).__new__(mcs, name, bases, dict_)

    def __init__(cls, name, bases, dict_):
        super(RuleSetDefinition, cls).__init__(name, bases, dict_)

        # Gather & initialize class definition objects:
        for (name, obj) in dict_.items():
            if isinstance(obj, Decision):
                obj.name = obj.name or name.lower()
                obj.owner = cls
                cls.decisions.add(obj)
            elif isinstance(obj, Rule):
                obj.owners.add(cls)
                cls.rules.append(obj)

    def __repr__(cls):
        return "<RuleSet: {}>".format(cls.__name__)


class RuleSet(object):

    __metaclass__ = RuleSetDefinition
    rules = decisions = None

    decision_required = True
    multiple_decisions = False

    @classmethod
    def rule(cls, func):
        """Decorator for the definition of Rules and their association with
        a RuleSet.

        RuleSet methods may be flagged as rules belonging to that set::

            class MyRuleSet(RuleSet):

                @RuleSet.rule
                def wears_pants(self):
                    if self.is_warm:
                        return self.PANTS

        In the above example, the RuleSet instance method is transformed into a
        Rule, and associated with the RuleSet by its metaclass.

        Simple functions may also be made into RuleSet Rules::

            @MyRuleSet.rule
            def wears_pants(context):
                ...

        In the latter example, the decorated function is replaced with Rule
        object and associated with the decorating RuleSet.

        """
        if cls is RuleSet:
            return Rule(func)

        rule_ = Rule(func)
        rule_.owners.add(cls)
        cls.rules.append(rule_)
        return rule_

    @classmethod
    def apply(cls, *args, **kws):
        """Initialize the RuleSet from the given arguments and apply its Rules,
        to return a decision.

        """
        self = cls(*args, **kws)
        return self.decide()

    def decide(self):
        """Iterate over the RuleSet object's Rules to return a decision."""
        made_decisions = []
        for rule in self.rules:
            decision = rule(self)
            if decision is not None:
                if self.decisions and decision not in self.decisions:
                    raise self.UnexpectedDecision(decision)

                try:
                    made_decision = decision.bind(rule)
                except AttributeError:
                    # Not using decision api:
                    made_decision = decision

                if self.multiple_decisions:
                    made_decisions.append(made_decision)
                else:
                    return made_decision

        if self.decision_required and not made_decisions:
            raise self.IndecisionError(self)
        return made_decisions

    class DecisionError(Exception):
        pass

    class UnexpectedDecision(DecisionError):
        pass

    class IndecisionError(DecisionError):
        pass

    def __str__(self):
        return "{} {!r}".format(self.__class__.__name__, vars(self))

    def __repr__(self):
        return "<RuleSet: {}>".format(self)


def context(func=None,
            decisions=None,
            decision_required=True,
            multiple_decisions=False):
    """Decorator (factory) to manufacture RuleSets from context-definition
    functions.

    The decorated function defines the interface of a new RuleSet, and constructs
    a context dictionary, which will be passed to the RuleSet's Rules as an
    object, the RuleSet instance bound to the context).

    For example, the following::

        class Classifier(RuleSet):

            def __init__(self, text):
                self.text = text

    may be achieved with::

        @context
        def classify(text):
            return {'text': text}

    and the result is a full-fledged RuleSet::

        @classify.rule
        def funny(context):
            if context.text:
                return 'funny'

        classify.apply("who's on first?")

    would result in `'funny'`.

    """
    def decorator(func):
        def init(self, *args, **kws):
            context_ = func(*args, **kws)
            vars(self).update(context_)

        return type(func.__name__, (RuleSet,), {
            '__init__': init,
            'decisions': decisions or set(),
            'decision_required': decision_required,
            'multiple_decisions': multiple_decisions,
            '__module__': func.__module__,
        })

    if func:
        return decorator(func)
    return decorator
