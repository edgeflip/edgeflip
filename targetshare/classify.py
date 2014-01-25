"""Functional RuleSet for the classification of a given corpus.

For example::

    classify.apply('A pudding cup is the perfect lunch idea or '
                   'wholesome snack for your kids.')

might result in::

    {'food': 0.313, 'children': 0.125}

"""
import collections
import functools
import numbers

from targetshare.utils import atan_norm
from targetshare.utils.rule import context


def reduce_topics(results):
    """Reduce the results of the classification rule set to a dictionary of
    normalized weights.

    [('topic', 0.44), ...] => {'topic': 0.012, ...}

    For use as the `RuleSet.resolve` postprocessor of `classify`.

    """
    scores = collections.defaultdict(int)
    for result in results:
        for (topic, score) in result:
            scores[topic] += score
    return {topic: atan_norm(score) for (topic, score) in scores.iteritems()}


@context(decision_required=False, multiple_decisions=True, resolve=staticmethod(reduce_topics))
def classify(corpus, topic=None):
    """Classify the given corpus, according to the RuleSet's classification
    rules, returning the content's topics and their normalized weights.

        corpus: a string of content to classify
        topic: a topic string or sequence of topic strings to which to limit
            classification (optional)

    Returns a dict of topics and their normalized weights.

    For example::

        classify.apply('fiber')

    might result in::

        {'health': 0.125}

    """
    # Return a mapping for use in initializing the RuleSet/context
    if isinstance(topic, basestring):
        topics = {topic}
    elif topic is None or isinstance(topic, set):
        topics = topic
    else:
        topics = set(topic)

    return {'corpus': corpus, 'topics': topics}


All = object()

WEIGHT_TYPES = (numbers.Number, basestring)


def classifier(func=None, topics=None):
    """Decorator (factory) for classification rules.

    Extends `classify.rule` to skip classifiers for deselected topics and
    ensure the structure of their results.

    Rules specify the topics they identify with the `topics` argument, which may
    be `All`. If unspecified, `topics` is the name of the rule.

    Rules named after the topic they identify may merely return the corpus's
    weight in that topic. Otherwise, rules must return the pair `(TOPIC, WEIGHT)`,
    or a stream of such pairs.

    """
    def decorator(func):
        @functools.wraps(func)
        def wrapped(context):
            name = func.__name__
            if (
                context.topics is None or
                topics is All or
                (topics is None and name in context.topics) or
                (topics and context.topics.intersection(topics))
            ):
                result = func(context)
                if not result:
                    return ()
                elif isinstance(result, WEIGHT_TYPES):
                    return [(name, result)]
                elif (
                    isinstance(result, (tuple, list)) and
                    len(result) == 2 and
                    isinstance(result[1], WEIGHT_TYPES)
                ):
                    return [result]
                else:
                    return result

        return classify.rule(wrapped)

    if func:
        return decorator(func)
    return decorator


# TODO: map dumb csv to:
SIMPLE_WEIGHTS = {
    'health': {
        'weights': {'fiber': 0.4, 'calories': 0.4, 'breast cancer': 0.1},
        'skip': (),
    },
    'lgbt': {
        'weights': {'gay pride': 0.8},
        'skip': ('chicago bears',),
    }
}


@classifier(topics=All)
def simple_map(context):
    """Classify corpus based on number of occurrences of words and phrases, and their
    weights, in the SIMPLE_WEIGHTS dictionary.

    """
    topics = SIMPLE_WEIGHTS.iterkeys() if context.topics is None else context.topics
    for topic in topics:
        try:
            topic_weights = SIMPLE_WEIGHTS[topic]
        except KeyError:
            continue

        skip = topic_weights.get('skip', ())
        if any(phrase in context.corpus for phrase in skip):
            continue

        count = 0
        weights = topic_weights.get('weights', {})
        for (phrase, weight) in weights.iteritems():
            count += context.corpus.count(phrase) * weight

        if count:
            yield (topic, count)


# Fake/example rules #

# @classifier
# def sports(context):
#     if 'football' in context.corpus.lower():
#         return '1.0'


# @classifier
# def health(context):
#     if 'calories' in context.corpus.lower():
#         return '1.0'
#     if 'fiber' in context.corpus.lower():
#         return '0.5'
