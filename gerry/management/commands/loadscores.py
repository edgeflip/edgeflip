import csv
import collections
import heapq
import itertools
import numbers
import os.path
import re
import urllib2
import sys
import tempfile
import time
import urlparse
from contextlib import closing
from decimal import Decimal
from operator import attrgetter
from optparse import make_option
from cStringIO import StringIO
from textwrap import dedent
from unidecode import unidecode

from django.core.management.base import BaseCommand, CommandError
from faraday.utils import cached_property

from gerry import models


# Generic utils #

def xmultireadlines(path, **netkws):
    """Open the the resource at the given local or remote path, returning an
    iterable stream of its lines.

    """
    if netreadlines.network_pattern.match(path):
        return netreadlines(path, **netkws)
    return readlines(path)


def readlines(path):
    """Generate lines from the file at the given path, ensuring that the handle
    is closed upon completion.

    """
    with open(os.path.expanduser(path), 'r') as fh:
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

netreadlines.network_pattern = re.compile(r'^[a-zA-Z]*://')


class CachedUnseekableFile(object):

    def __init__(self, stream):
        self.stream = stream
        self.cache = tempfile.TemporaryFile()

    def reset(self):
        if self.stream is not None:
            raise ValueError("input stream not fully cached")

        self.cache.seek(0)

    def __iter__(self):
        return self

    def next(self):
        if self.stream is None:
            return next(self.cache)

        try:
            line = next(self.stream)
        except StopIteration:
            self.stream = None
            raise
        else:
            self.cache.write(line)
            self.cache.flush()
            return line


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


# Voter registration model #

VOTER_FEATURES = collections.OrderedDict([
    # (feature name, possible input names)
    ('state', ['regstate']),
    ('city',  ['regcity']),
    ('lname',  ['lastname']),
    ('fname',  ['firstname']),
    ('gotv_score',  ['gotv_2014']),
    ('persuasion_score',  ['persuasion_score_dnc']),
])


VoterRegistrationBase = collections.namedtuple('VoterRegistrationBase', VOTER_FEATURES)


class VoterRegistration(VoterRegistrationBase):

    # Extend basic namedtuple to normalize inputs

    __slots__ = ()

    @staticmethod
    def _clean_score(value):
        if isinstance(value, numbers.Number):
            return value
        elif value:
            return Decimal(value)
        else:
            return None

    @staticmethod
    def _clean_feature(value):
        # Translate UTF-8 unicode to reasonable ASCII
        # (models.normalize already does this; however, let's be eager,
        # for nickname look-up)
        decoded = value.decode('utf-8')
        unidecoded = unidecode(decoded)
        return unidecoded.upper()

    @classmethod
    def _clean_inputs(cls, inputs):
        for (key, value) in inputs:
            if key.endswith('score'):
                yield (key, cls._clean_score(value))
            else:
                yield (key, cls._clean_feature(value))

    @classmethod
    def _make(cls, iterable):
        cleaned = cls._clean_inputs(itertools.izip(cls._fields, iterable))
        return super(VoterRegistration, cls)._make(value for (_key, value) in cleaned)

    def __new__(cls, *args, **kws):
        normalized = itertools.chain(itertools.izip(cls._fields, args), kws.iteritems())
        cleaned = cls._clean_inputs(normalized)
        return super(VoterRegistration, cls).__new__(cls, **dict(cleaned))

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join('{}={!r}'.format(key, value)
                    for key, value in itertools.izip(self._fields, self))
        )


# Shell command #

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

    nicknames_path = 'http://edgeflip-misc.s3.amazonaws.com/nicknames.csv'

    option_list = BaseCommand.option_list + (
        make_option('--nonicks', action='store_false', default=True, dest='include_nicknames',
            help='Disable creation of additional listings for entries with recognized nicknames'),
        make_option('--nicknames', default=nicknames_path, dest='nicknames_path',
            help="Local or remote path from which to populate nickname look-ups "
                 "[default: `{}']".format(nicknames_path)),
    )

    def __init__(self):
        super(Command, self).__init__()
        self.stdin = sys.stdin
        self.incache = None
        self.headermap = None
        self.verbosity = None
        self.nicknames = {}

    @cached_property
    def headermap_reversed(self):
        indexes_reversed = sorted(
            (header_index, internal_index)
            for (internal_index, header_index) in enumerate(self.headermap)
        )
        filled = []
        filler = [None]
        last_index = -1
        for (header_index, internal_index) in indexes_reversed:
            # Fill in gaps with None:
            filled += filler * (header_index - last_index - 1)
            # Add internal index for this column:
            filled.append(internal_index)
            last_index = header_index
        return filled

    def populate_nicknames(self, path):
        for row in csv.DictReader(xmultireadlines(path)):
            key = row['name'].upper()
            value = row['nickname'].upper()
            collection = self.nicknames.setdefault(key, set())
            collection.add(value)

    def pout(self, msg, verbosity=1):
        """Write the given string to stdout as allowed by the verbosity."""
        if self.verbosity >= verbosity:
            self.stdout.write(msg)

    def perr(self, msg, verbosity=1):
        """Write the given string to stderr as allowed by the verbosity."""
        if self.verbosity >= verbosity:
            self.stderr.write(msg)

    def parselines(self, lines):
        for row in csv.reader(lines):
            yield VoterRegistration._make(row[index] for index in self.headermap)

    def parse(self, line):
        try:
            (registration,) = self.parselines((line,))
        except (csv.Error, StopIteration, ValueError):
            self.perr("Parse failed: {!r}".format(line))
            return None
        else:
            return registration

    def encodelines(self, objs):
        target = StringIO()
        writer = csv.writer(target)
        for obj in objs:
            # Write empty str for values we don't store (i.e. index is None)
            # AND for empty values we stored as None
            values = (None if index is None else obj[index]
                      for index in self.headermap_reversed)
            writer.writerow(['' if value is None else str(value) for value in values])
        target.seek(0)
        return target

    def handle(self, path=None, **options):
        self.verbosity = int(options['verbosity'])

        if options['include_nicknames']:
            self.populate_nicknames(options['nicknames_path'])

        for model in models.LOOKUPS:
            stream = self.initialize_stream(path)

            self.ingest_header(stream)

            # Duplicate rows across nicknames if requested
            full_stream = self.nickname_expand(stream) if options['include_nicknames'] else stream

            # csv -> :sort -> :groupby => [{signature: SIG, score0: min(feature0), ...}, ...]
            score_lookups = self.generate_lookups(model, full_stream)

            # -> :insert
            self.persist_lookups(model, score_lookups)

    def initialize_stream(self, path):
        if path is None:
            if self.incache is None:
                try:
                    self.stdin.seek(0)
                except IOError as exc:
                    if exc.errno == 29:
                        # non-seekable input (e.g. pipe)
                        self.incache = CachedUnseekableFile(self.stdin)
                        return self.incache
                    raise
                else:
                    return self.stdin
            else:
                self.incache.reset()
                return self.incache
        else:
            return xmultireadlines(path)

    def ingest_header(self, stream):
        """Strip header from input CSV stream and determine column indexes for
        VoterRegistration features.

        """
        header = next(stream)
        if self.headermap is not None:
            return

        self.pout("Header is:\n\t{}".format(header))
        columns = header.lower().strip().split(',')

        self.headermap = []
        for (voter_feature, possibilities) in VOTER_FEATURES.iteritems():
            for possibility in possibilities:
                try:
                    # Look up position of feature in input
                    index = columns.index(possibility)
                except ValueError:
                    # No luck, try next external name possibility
                    pass
                else:
                    # Store where to find this feature
                    self.headermap.append(index)
                    break # on to the next feature
            else:
                # Known possiblities exhausted
                raise CommandError('Failed to find "{}" column in header '
                                   '(tried: {!r})'.format(voter_feature, possibilities))

    def nickname_expand(self, stream):
        """Stream given voter registration rows along with their duplicates for
        each nickname.

        """
        # Keep original and nickname row in CSV string format for easy input
        # into batch_sort
        for row in stream:
            yield row

            formal = self.parse(row)
            try:
                nicknames = self.nicknames[formal.fname]
            except KeyError:
                continue

            renamed = (formal._replace(fname=nickname) for nickname in nicknames)
            for reencoded in self.encodelines(renamed):
                yield reencoded

    def make_extractor(self, model):
        """Manufacture a callable which, given a line of voter registration CSV,
        produces its look-up key for the given model.

        """
        def extract(line):
            registration = self.parse(line)
            return model.extract_hash(registration) if registration else None
        return extract

    def generate_lookups(self, model, stream):
        extractor = self.make_extractor(model)
        sorted_stream = batch_sort(stream, key=extractor, retain_key=True)
        for (lookup_key, group) in itertools.groupby(sorted_stream, attrgetter('key')):
            if lookup_key is None:
                self.perr("Skipping group of {} rows without signature"
                          .format(sum(1 for element in group)))
                continue

            # Build aggregate scores for group of registrations sharing look-up signature
            score_lookup = {model.hashkey: lookup_key}
            rows = (keyed.obj for keyed in group)
            registrations = tuple(self.parselines(rows))
            for feature in models.SUPPORTED_FEATURES:
                values = (getattr(registration, feature) for registration in registrations)
                scores = [value for value in values if value is not None]
                if scores:
                    score_lookup[feature] = min(scores)

            if len(score_lookup) == 1:
                # Empty besides hash key, no reason to insert
                continue

            yield score_lookup

    def persist_lookups(self, model, score_lookups):
        with model.items.batch_write() as batch:
            for score_lookup in score_lookups:
                batch.put_item(score_lookup)
