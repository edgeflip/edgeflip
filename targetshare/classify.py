"""Quick-and-dirty text classifier based on phrase weights in CSV.

For example::

    classify('A pudding cup is the perfect lunch idea or '
             'wholesome snack for your kids.')

might result in::

    {'food': 0.313, 'children': 0.125}

"""
import collections
import csv
import itertools
import re

from targetshare.utils import atan_norm


class SimpleWeights(dict):

    __slots__ = ()

    COLUMNS = ('topic', 'phrase', 'weight', 'skip')

    AbstractPhraseWeight = collections.namedtuple('AbstractPhraseWeight', COLUMNS[1:] + ('pattern',))

    class PhraseWeight(AbstractPhraseWeight):

        __slots__ = ()

        def __new__(cls, phrase, weight, skip, pattern=None):
            if pattern is None:
                space_optional = re.sub(r'\s+', r'\s*', phrase)
                pattern = re.compile(r'\b{}\b'.format(space_optional), re.I)
            return super(SimpleWeights.PhraseWeight, cls).__new__(cls, phrase, weight, skip, pattern)

        def __repr__(self):
            return '<{}: {!r} [{}]>'.format(
                self.__class__.__name__,
                self.phrase,
                'SKIP' if self.skip else self.weight,
            )

        def get_phrase_weight(self, corpus):
            count = 0

            for match in self.pattern.finditer(corpus):
                if self.skip:
                    raise SimpleWeights.SkipPhrase(self.phrase, match)

                count += self.weight

            return count

    class SkipPhrase(Exception):
        pass

    @classmethod
    def _read(cls, handle):
        reader = csv.reader(handle)

        # Check for header row:
        start = next(reader)
        if any(value != column_name for (column_name, value) in itertools.izip(cls.COLUMNS, start)):
            # No header, this looks like a data row
            yield start

        for row in reader:
            yield row

    @classmethod
    def load(cls, handle):
        self = cls()

        for (topic, phrase, weight, skip) in cls._read(handle):
            weight = float(weight) if weight else None
            skip = bool(int(skip))
            phrase_list = self.setdefault(topic, [])
            phrase_list.append(cls.PhraseWeight(phrase, weight, skip))

        return self

    def iter_topics(self, corpus, *topics):
        for topic in (topics or self.iterkeys()):
            weight = 0
            for phrase_info in self.get(topic, ()):
                try:
                    weight += phrase_info.get_phrase_weight(corpus)
                except self.SkipPhrase:
                    yield (topic, 0)
                    break
            else:
                yield (topic, weight)

    def classify(self, corpus, *topics):
        """Classify `corpus` based on number of occurrences of words and phrases, and their
        weights, in the SimpleWeights dictionary.

        By default, `corpus` is classified for all topics for which there are weights.
        Alternatively, topics may be specified as arbitrary arguments:

            SIMPLE_WEIGHTS.classify(corpus, 'healthcare', 'cooking', ...)

        """
        return {topic: atan_norm(score) for (topic, score) in self.iter_topics(corpus, *topics)}

SIMPLE_WEIGHTS = SimpleWeights.load(open('topics.csv')) # FIXME
classify = SIMPLE_WEIGHTS.classify
