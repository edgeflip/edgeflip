import functools

from targetshare.utils.rule import context


@context(decision_required=False, multiple_decisions=True)
def classify(corpus, topic=None):
    """Classify the given corpus, according to the RuleSet's classification
    rules, returning the content's topics and their absolute weights.

        corpus: a string of content to classify
        topic: a topic string or sequence of topic strings to which to limit
            classification (optional)

    Returns a list of topics and their absolute weights.

    """
    topics = (topic,) if isinstance(topic, basestring) else topic
    return {'corpus': corpus, 'topics': topics}


def classifier(func):
    @functools.wraps(func)
    def wrapped(context):
        name = func.__name__
        if context.topics is None or name in context.topics:
            result = func(context)
            return result if result is None else (name, result)
    return classify.rule(wrapped)


# Fake/example rules #

@classifier
def sports(context):
    if 'football' in context.corpus.lower():
        return '1.0'


@classifier
def health(context):
    if 'calories' in context.corpus.lower():
        return '1.0'
    if 'fiber' in context.corpus.lower():
        return '0.5'
