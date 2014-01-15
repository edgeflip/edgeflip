"""A framework for the definition and application of rule sets."""
import functools


class Rule(object):
    """A callable member of the RuleSet.

    Rule wraps stand-alone functions and object methods. (See `RuleSet.rule`.)

    """
    def __init__(self, func):
        self.func = func
        self.owners = set()

        functools.update_wrapper(self, self.func, updated=())
        for (key, value) in vars(self.func).items():
            vars(self).setdefault(key, value)

    def contribute_to_class(self, rule_set, name=None):
        self.owners.add(rule_set)
        return self

    def __call__(self, context):
        return self.func(context)

    def __get__(self, instance, cls):
        if instance is None:
            return self

        @functools.wraps(self)
        def bound():
            return self(instance)
        return bound

    def __repr__(self):
        return "{}({}.{})".format(self.__class__.__name__,
                                  self.__module__,
                                  self.__name__)

    def __str__(self):
        return self.__name__


class Decision(object):
    """A Rule execution result.

    Decisions may optionally be defined for the RuleSet, and are then available
    for selection by the Rule. (See `RuleSet`.)

    """
    is_bound = False

    def __init__(self, name=None, **meta):
        self.name = name
        self.meta = meta
        self.accessor = None
        self.owner = None

    def contribute_to_class(self, rule_set, name=None):
        if name is None:
            obj = type(self)(self.name, **self.meta)
            obj.accessor = self.accessor
        else:
            obj = self
            if not obj.name:
                obj.name = name.lower()
            obj.accessor = name

        obj.owner = rule_set
        return obj

    def bind(self, rule):
        return BoundDecision(name=self.name,
                             owner=self.owner,
                             made_by=rule,
                             **self.meta)

    def __hash__(self):
        return hash((self.owner, self.name))

    def __eq__(self, other):
        return (isinstance(other, Decision) and
                other.owner == self.owner and
                other.name == self.name)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "<{}(name={!r}) on {}>".format(self.__class__.__name__,
                                              self.name,
                                              self.owner)


class BoundDecision(Decision):
    """A Rule-selected Decision.

    BoundDecision extends the RuleSet's Decision with information about the
    Rule that selected it.

    """
    is_bound = True

    def __init__(self, name, owner, made_by, **meta):
        super(BoundDecision, self).__init__(name, **meta)
        self.owner = owner
        self.made_by = made_by

    def __eq__(self, other):
        eq = super(BoundDecision, self).__eq__(other)
        if isinstance(other, BoundDecision):
            return eq and other.made_by == self.made_by
        return eq

    def __repr__(self):
        return "{}(name={!r}, owner={!r}, made_by={!r})".format(
            self.__class__.__name__,
            self.name,
            self.owner,
            self.made_by,
        )


class DecisionAccessor(object):
    """Descriptor providing easy access to the appropriate RuleSet Decision.

    The RuleSet inheritance model relies on the sharing of Rules, but Decisions
    remain attached to their RuleSet; to ensure that inherited RuleSet class
    attributes refer to the appropriate Decisions, Decisions specified in the
    RuleSet class definition are stored canonically in the class's "decisions"
    set, and these attribute references are replaced with this descriptor.

    To supply some level of caching, when accessed through the RuleSet instance,
    the result of the descriptor's look-up in the class is stored on the
    instance, (and subsequent access through the instance will prefer its
    dictionary to the descriptor).

    """
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, cls):
        for decision in cls.decisions:
            if decision.accessor == self.name:
                break
        else:
            raise LookupError("Decision {} missing from {}".format(self.name, cls))

        if instance is not None:
            # Cache decision on instance:
            setattr(instance, self.name, decision)

        return decision


class RuleSetDefinition(type):
    """RuleSet metaclass.

    This metaclass ensures the structure and inheritance of Decisions and Rules
    and handles the specification of these during RuleSet class definition.
    (See `RuleSet`.)

    """
    def __init__(cls, name, bases, dict_):
        super(RuleSetDefinition, cls).__init__(name, bases, dict_)

        # Handle inherited (and explicitly set) definitions:
        for (name, default) in [
            ('decisions', set()),
            ('rules', []),
        ]:
            items = getattr(cls, name, None)
            if items:
                value = type(items)(item.contribute_to_class(cls) for item in items)
            else:
                value = default
            setattr(cls, name, value)

        # Pick up novel definitions in class dict:
        for (name, obj) in dict_.items():
            try:
                contributor = obj.contribute_to_class
            except AttributeError:
                continue

            value = contributor(cls, name)

            if isinstance(obj, Decision):
                cls.decisions.add(value)
                setattr(cls, name, DecisionAccessor(name))
            elif isinstance(obj, Rule):
                cls.rules.append(value)
                setattr(cls, name, value)

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
        rule_ = Rule(func)

        if cls is RuleSet:
            return rule_

        rule_.owners.add(cls)
        cls.rules.append(rule_)
        return rule_

    def apply(cls, *args, **kws):
        """Initialize the RuleSet from the given arguments and apply its Rules,
        to return a decision.

        """
        self = cls(*args, **kws)
        return self.decide()

    def __repr__(cls):
        return "<{}>".format(cls)

    def __str__(cls):
        return "RuleSet: {}".format(cls.__name__)


class RuleSet(object):

    __metaclass__ = RuleSetDefinition
    rules = decisions = None

    decision_required = True
    multiple_decisions = False

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
            decision_required=True,
            multiple_decisions=False,
            rule_set_cls=RuleSet,
            **decisions):
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

        defn = {
            '__init__': init,
            'decision_required': decision_required,
            'multiple_decisions': multiple_decisions,
            '__module__': func.__module__,
            '__doc__': func.__doc__,
        }
        defn.update(decisions)

        return type(func.__name__, (rule_set_cls,), defn)

    if func:
        return decorator(func)
    return decorator
