import csv
import collections
import heapq
import itertools
import os.path
import re
import urllib2
import sys
import tempfile
import time
import urlparse
from operator import attrgetter
from textwrap import dedent

from django.core.management.base import BaseCommand
from faraday.structs import LazySequence

from gerry import models


NETWORK_PATTERN = r'^[a-zA-Z]*://'


def netreadlines(url, cache_time=(5 * 3600)):
    """Line-wise stream generator for networked resources.

    By default, documents are cached in a temporary directory; and on invocation,
    cached documents younger than `cache_time` are returned, rather than retrieving the
    remote document. To ignore the cache, set `cache_time=0`.

    """
    result = urlparse.urlparse(url)
    filename = '{}-{}'.format(result.netloc, result.path.strip('/').replace('/', '-'))
    cachepath = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(cachepath) and time.time() - os.path.getmtime(cachepath) < cache_time:
        for line in open(cachepath, 'r'):
            yield line
        return

    with open(cachepath, 'w') as cachefh:
        for line in urllib2.urlopen(url):
            cachefh.write(line)
            yield line


Keyed = collections.namedtuple('Keyed', ('key', 'obj'))


def batch_sort(iterable, key=None, retain_key=False, buffer_size=(32 * 1024)):
    chunks = []
    stream = iter(iterable)

    def get_batch():
        return sorted(itertools.islice(stream, buffer_size), key=key)

    try:
        # Write input into individually-sorted tempfile chunks:
        for chunk in iter(get_batch, []):
            temp = tempfile.TemporaryFile(suffix='-sort')
            temp.writelines(chunk)
            temp.flush()
            temp.seek(0)
            chunks.append(temp)

        # Merge the chunks, sorted, and stream the lines:
        keyed_chunks = (
            (Keyed((key and key(line)), line) for line in chunk)
            for chunk in chunks
        )
        for keyed in heapq.merge(*keyed_chunks):
            yield keyed if retain_key else keyed.obj

    finally:
        for temp in chunks:
            try:
                temp.close()
            except Exception:
                pass


class MethodRegistry(list):
    """Method registration list, providing a decorator entrypoint, and
    descriptor-binding retrieval.

    """
    class BoundMethods(LazySequence):

        @classmethod
        def bind(cls, instance, funcs):
            return cls(func.__get__(instance) for func in funcs)

    def __call__(self, func):
        """Decorator-style registration entrypoint."""
        self.append(func)
        return func

    def __get__(self, instance, cls=None):
        """When accessed as a class attribute, the registry is returned as is;
        when accessed as an instance attribute, a lazy collection is returned
        which binds the registered methods to the instance.

        """
        if instance is None:
            return self

        return self.BoundMethods.bind(instance, self)


class Command(BaseCommand):

    args = '[PATH]'
    help = dedent("""\
        Reduce an input CSV of scored voter registrations by a set of look-up keys,
        paired with their minimum voter "GOTV" and "persuasion" scores by group, and
        load scores into DynamoDB.

        Current look-up keys:
            state_lname_fname (regstate, lastname, firstname)
            state_city_lname_fname (regstate, regcity, lastname, firstname)

        Current scores:
            persuasion_score (persuasion_score_dnc)
            gotv_score (gotv_2014)

        """).strip()

    def __init__(self):
        super(Command, self).__init__()
        self.header = None
        self.verbosity = None

    def pout(self, msg, verbosity=1):
        """Write the given string to stdout as allowed by the verbosity."""
        if self.verbosity >= verbosity:
            self.stdout.write(msg)

    def perr(self, msg, verbosity=1):
        """Write the given string to stderr as allowed by the verbosity."""
        if self.verbosity >= verbosity:
            self.stderr.write(msg)

    def handle(self, path=None, **options):
        self.verbosity = int(options['verbosity'])

        for lookup_key in self.LOOKUP_KEYS:
            if path is None:
                sys.stdin.seek(0)
                stream = sys.stdin
            elif re.search(NETWORK_PATTERN, path):
                stream = netreadlines(path)
            else:
                stream = open(path, 'r')

            header = next(stream)
            if self.header is None:
                self.pout("Header is:\n\t{}".format(header))
                self.header = header.strip().split(',')

            # sort -> groupby -> [{signature: SIG, score0: min(feature0), ...}, ...]
            score_lookups = self.handle_key(lookup_key, stream)

            # -> insert
            self.persist_scores(lookup_key, score_lookups)

    def handle_key(self, key, stream):
        sorted_stream = batch_sort(stream, key, retain_key=True)
        for (signature, group) in itertools.groupby(sorted_stream, attrgetter('key')):
            if signature is None:
                self.perr("Skipping group of {} rows without signature"
                          .format(sum(1 for element in group)))
                continue

            score_lookup = {key.__name__: signature}
            rows = (keyed.obj for keyed in group)
            registrations = tuple(csv.DictReader(rows, self.header))
            for (feature_code, feature) in (('persuasion_score_dnc', 'persuasion_score'),
                                            ('gotv_2014', 'gotv_score')):
                scores = [score for score in (
                    registration[feature_code] for registration in registrations
                ) if score] # ignore empties
                if scores:
                    score_lookup[feature] = min(scores)

            yield score_lookup

    def persist_scores(self, lookup_key, score_lookups):
        with lookup_key.model.items.batch_write() as batch:
            for score_lookup in score_lookups:
                batch.put_item(score_lookup)

    lookupkey = LOOKUP_KEYS = MethodRegistry()

    def _extract_key(self, line, features):
        try:
            (registration,) = csv.DictReader((line,), self.header)
        except (csv.Error, StopIteration):
            self.perr("Parse failed: {!r}".format(line))
            return None

        return '_'.join(registration[feature].upper().replace(' ', '-')
                        for feature in features)

    @lookupkey
    def state_lname_fname(self, line):
        return self._extract_key(line, ('regstate', 'lastname', 'firstname'))
    state_lname_fname.model = models.StateNameVoter

    @lookupkey
    def state_city_lname_fname(self, line):
        return self._extract_key(line, ('regstate', 'regcity', 'lastname', 'firstname'))
    state_city_lname_fname.model = models.StateCityNameVoter
