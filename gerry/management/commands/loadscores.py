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
from contextlib import closing
from operator import attrgetter
from optparse import make_option
from textwrap import dedent

from django.core.management.base import BaseCommand
from faraday.structs import LazySequence

from gerry import models


NETWORK_PATTERN = r'^[a-zA-Z]*://'
NICKNAMES_PATH = 'http://edgeflip-misc.s3.amazonaws.com/nicknames.csv'


def readlines(path):
    """Generate lines from the file at the given path, ensuring that the handle
    is closed upon completion.

    """
    with open(path, 'r') as fh:
        for line in fh:
            yield line


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
        with open(cachepath, 'r') as cachefh:
            for line in cachefh:
                yield line
        return

    with open(cachepath, 'w') as cachefh:
        with closing(urllib2.urlopen(url)) as response:
            for line in response:
                cachefh.write(line)
                yield line


def batch_sort(iterable, key=None, retain_key=False, buffer_size=(32 * 1024)):
    """Sort the given iterable of strings, in batches (heap sort), storing
    batches on disk.

    Results are returned as a stream. Use this method to sort a large
    collection, to avoid constraints of memory.

    """
    # Note: this could be extended to sort any pickleable object, though that's
    # currently unnecessary.
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

        # Merge the chunks, sorted, and stream the lines
        # (heapq accepts no sort key, so we wrap the lines in Keyed)
        keyed_chunks = (
            (batch_sort.Keyed((key and key(line)), line) for line in chunk)
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

batch_sort.Keyed = collections.namedtuple('Keyed', ('key', 'obj'))


class MethodRegistry(list):
    """Method registration list, providing a decorator entrypoint, and
    descriptor-binding retrieval.

    For example, with the registry instantiated in the class definition as:

        lookupkey = LOOKUP_KEYS = MethodRegistry()

    methods may be registered as:

        @lookupkey
        def my_key(self, row):
            ...

    and later inspected by other methods:

        def my_method(self):
            for lookup_key in self.LOOKUP_KEYS:
                ...

    When the registry is retrieved from an instance of a class of which it is
    an attribute, as above, the registered methods are returned already bound,
    as though they were retrieved by direct attribute access,
    (e.g. `self.my_key`).

    Note that the registry may be instantiated, and functions defined and
    registered, anywhere; registered functions are bound as methods, indirectly
    when the registry is accessed as an instance attribute, or directly via the
    registry's __get__ method.

    """
    class BoundMethods(LazySequence):

        @classmethod
        def bind(cls, instance, funcs):
            return cls(func.__get__(instance) for func in funcs)

    def register(self, func):
        """Decorator-style registration entrypoint."""
        self.append(func)
        return func

    def __call__(self, func):
        """Decorator-style registration entrypoint."""
        return self.register(func)

    def __get__(self, instance, cls=None):
        """When accessed as a class attribute, the registry is returned as is;
        when accessed as an instance attribute, a lazy collection is returned
        which binds the registered methods to the instance.

        """
        if instance is None:
            return self

        return self.BoundMethods.bind(instance, self)


class LookupMethod(object):

    def __init__(self, model, columns):
        self.model = model
        self.columns = columns
        self._features = dict(zip(columns, model.keyfeatures))

    @property
    def name(self):
        return self.model.hashkey
    __name__ = name

    def make(self, registration):
        # Rather than map input header's column names to ours on parse (which
        # we could still do), extract value here and send internally-recognized
        # name to normalizer:
        return self.model.delimiter.join(
            models.normalize(self._features[column], registration[column])
            for column in self.columns
        )

    def extract(self, command, line):
        registration = command.parse(line)
        if registration is None:
            return None
        else:
            return self.make(registration)

    def __call__(self, *args, **kws):
        return self.extract(*args, **kws)

    def __get__(self, command, cls=None):
        if command is None:
            return self

        return BoundLookupMethod(self.model, self.columns, command)


class BoundLookupMethod(LookupMethod):

    def __init__(self, model, columns, command):
        super(BoundLookupMethod, self).__init__(model, columns)
        self.command = command

    def extract(self, line):
        return super(BoundLookupMethod, self).extract(self.command, line)


class LookupRegistry(MethodRegistry):

    def __init__(self, iterable):
        super(LookupRegistry, self).__init__(LookupMethod(*item) for item in iterable)


LOOKUP_METHODS = LookupRegistry([
    (models.StateNameVoter, ['regstate', 'lastname', 'firstname']),
    (models.StateCityNameVoter, ['regstate', 'regcity', 'lastname', 'firstname']),
])


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

    option_list = BaseCommand.option_list + (
        make_option('--nonicks', action='store_false', default=True, dest='include_nicknames',
            help='Disable creation of additional listings for entries with recognized nicknames'),
        make_option('--nicknames', default=NICKNAMES_PATH, dest='nicknames_path',
            help="Local or remote path from which to populate nickname look-ups "
                 "[default: `{}']".format(NICKNAMES_PATH)),
    )

    lookup_methods = LOOKUP_METHODS

    def __init__(self):
        super(Command, self).__init__()
        self.header = None
        self.verbosity = None
        self.nicknames = {}

    def pout(self, msg, verbosity=1):
        """Write the given string to stdout as allowed by the verbosity."""
        if self.verbosity >= verbosity:
            self.stdout.write(msg)

    def perr(self, msg, verbosity=1):
        """Write the given string to stderr as allowed by the verbosity."""
        if self.verbosity >= verbosity:
            self.stderr.write(msg)

    def populate_nicknames(self, path):
        stream = netreadlines(path) if re.search(NETWORK_PATTERN, path) else readlines(path)
        for row in csv.DictReader(stream):
            key = row['name'].upper()
            value = row['nickname'].upper()
            collection = self.nicknames.setdefault(key, set())
            collection.add(value)

    def parselines(self, lines):
        return csv.DictReader(lines, self.header)

    def parse(self, line):
        try:
            (registration,) = self.parselines((line,))
        except (csv.Error, StopIteration, ValueError):
            self.perr("Parse failed: {!r}".format(line))
            return None
        else:
            return registration

    def handle(self, path=None, **options):
        self.verbosity = int(options['verbosity'])

        if options['include_nicknames']:
            self.populate_nicknames(options['nicknames_path'])

        for lookup_method in self.lookup_methods:
            if path is None:
                sys.stdin.seek(0)
                stream = sys.stdin
            elif re.search(NETWORK_PATTERN, path):
                stream = netreadlines(path)
            else:
                stream = readlines(path)

            header = next(stream)
            if self.header is None:
                self.pout("Header is:\n\t{}".format(header))
                self.header = header.strip().split(',')

            # sort -> groupby -> [{signature: SIG, score0: min(feature0), ...}, ...]
            score_lookups = self.generate_lookups(lookup_method, stream)

            # -> insert
            self.persist_lookups(lookup_method.model, score_lookups)

    def generate_lookups(self, lookup_method, stream):
        key_name = lookup_method.name
        sorted_stream = batch_sort(stream, key=lookup_method, retain_key=True)
        for (lookup_key, group) in itertools.groupby(sorted_stream, attrgetter('key')):
            if lookup_key is None:
                self.perr("Skipping group of {} rows without signature"
                          .format(sum(1 for element in group)))
                continue

            # Build aggregate scores for group of registrations sharing look-up signature
            score_lookup = {key_name: lookup_key}
            rows = (keyed.obj for keyed in group)
            registrations = tuple(self.parselines(rows))
            for (feature_code, feature) in (('persuasion_score_dnc', 'persuasion_score'),
                                            ('gotv_2014', 'gotv_score')):
                values = (registration[feature_code] for registration in registrations)
                scores = [value for value in values if value] # ignore empties
                if scores:
                    score_lookup[feature] = min(scores)

            if len(score_lookup) == 1:
                # Empty besides hash key, no reason to insert
                continue

            yield score_lookup

            # Cross formal name look-up with nickname look-ups
            # All keys use firstname, and it will be shared across group:
            registration = registrations[0]
            firstname = registration['firstname']
            for nickname in self.nicknames.get(firstname.upper(), ()):
                nickname_registration = dict(registration, firstname=nickname)
                nickname_key = lookup_method.make(nickname_registration)
                yield dict(score_lookup, **{key_name: nickname_key})

    def persist_lookups(self, model, score_lookups):
        with model.items.batch_write() as batch:
            for score_lookup in score_lookups:
                batch.put_item(score_lookup)
