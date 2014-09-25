import csv
import collections
import heapq
import itertools
import os.path
import re
import urllib2
import sys
import tempfile
import urlparse
from textwrap import dedent

from django.core.management.base import BaseCommand


NETWORK_PATTERN = r'^[a-zA-Z]*://'


def netreadlines(url, cache=True, chunk_size=(16 * 1024)):
    """Line-wise stream generator for networked resources."""
    response = urllib2.urlopen(url)

    def get_chunk():
        return response.read(chunk_size)

    if cache:
        result = urlparse.urlparse(url)
        filename = '{}-{}'.format(result.netloc,
                                  result.path.strip('/').replace('/', '-'))
        cachepath = os.path.join(tempfile.tempdir, filename)

        if os.path.exists(cachepath):
            for line in open(cachepath, 'r'):
                yield line
            return
    else:
        cachepath = '/dev/null'

    with open(cachepath, 'w') as cachefh:
        # Re-chunk by line:
        line = ''
        for chunk in iter(get_chunk, ''):
            for byte in chunk:
                line += byte
                if byte == '\n':
                    cachefh.write(line)
                    yield line
                    line = ''

        # Yield any remainder (for files that do not end with newline):
        if line:
            cachefh.write(line)
            yield line


Keyed = collections.namedtuple('Keyed', ('key', 'obj'))


def batch_sort(iterable, key=None, buffer_size=(32 * 1024)):
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
            yield keyed.obj

    finally:
        for temp in chunks:
            try:
                temp.close()
            except Exception:
                pass


class LookupKeys(list):

    def __call__(self, func):
        self.append(func)
        return func

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        return [func.__get__(instance) for func in self]


class Command(BaseCommand):

    args = '[PATH]'
    help = dedent("""\
        Ask me later.

        """).strip()

    option_list = BaseCommand.option_list + (
        #make_option('--no-header', action='store_false', default=True, dest='discard_header',
        #            help="Retain first line of input (when there is no header)"),
    )

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
                self.header = header.split(',')

            self.handle_key(lookup_key, stream)

    def handle_key(self, key, stream):
        # TODO
        # sort -> groupby -> {signature: [min(key0), min(key1), ...]} -> insert
        sorted_stream = batch_sort(stream, key)
        for (signature, group) in itertools.groupby(sorted_stream, key):
            pass

    lookupkey = LOOKUP_KEYS = LookupKeys()

    @lookupkey
    def state_city_lname_fname(self, line):
        try:
            (registration,) = csv.DictReader((line,), self.header)
        except (csv.Error, StopIteration):
            self.perr("Parse failed: {!r}".format(line))
            return None

        return '_'.join(
            registration[feature] for feature in (
                'regstate',
                'regcity',
                'lastname',
                'firstname',
            )
        )
