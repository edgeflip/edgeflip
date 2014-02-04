import base64
import copy
import datetime
import functools
import itertools
import logging
import math
import random
import re
import sys
import time
import urllib
from Crypto.Cipher import DES
from StringIO import StringIO

from django.conf import settings


logger = logging.getLogger(__name__)


PADDING = ' '
BLOCK_SIZE = 8
MAX_MISSING_CIVIS_MATCHES = 20

pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

# DES appears to be limited to 8-character secret, so truncate if too long
secret = pad(settings.CRYPTO.des_secret)[:8]
cipher = DES.new(secret)


def atan_norm(value):
    """Normalize the given value to 1."""
    return math.atan(float(value) / 2) * 2 / math.pi


def camel_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class classonlymethod(classmethod):

    def __get__(self, instance, owner):
        if instance is not None:
            raise TypeError("Method available to class, not instances of {}.".format(owner))
        return super(classonlymethod, self).__get__(instance, owner)


class CDFProbsError(Exception):
    """CDF defined by provided experimental probabilities is not well-defined"""
    pass


def check_cdf(sequence):
    """Takes tuples of (id, CDF Probability) and ensures the CDF is well-defined"""
    probs = sorted(pair[1] for pair in sequence)
    if min(probs) <= 0:
        raise CDFProbsError("Zero or negative probabilities detected")
    if max(probs) != 1.0:
        raise CDFProbsError("Max probability is not 1.0")
    if len(probs) != len(set(probs)):
        raise CDFProbsError("Duplicate values found in CDF")


def random_assign(sequence):
    """Randomly assign an element from a sequence of elements paired with their
    CDF probabilities.

    """
    # Ensure sorted by CDF probability:
    sorted_ = sorted(sequence, key=lambda pair: pair[1])
    check_cdf(sorted_)

    # Pick out smallest probability greater than or equal to random number:
    rand = random.random()
    for obj_id, prob in sorted_:
        if prob >= rand:
            return obj_id

    raise CDFProbsError("Math must be broken if we got here...")


def encodeDES(message):
    """Encrypt a message with DES cipher, returning a URL-safe, quoted string"""
    message = str(message)
    encrypted = cipher.encrypt(pad(message))
    b64encoded = base64.urlsafe_b64encode(encrypted)
    encoded = urllib.quote(b64encoded)
    return encoded


def decodeDES(encoded):
    """Decrypt a message with DES cipher, assuming a URL-safe, quoted string"""
    encoded = str(encoded)
    unquoted = urllib.unquote(encoded)
    b64decoded = base64.urlsafe_b64decode(unquoted)
    message = cipher.decrypt(b64decoded).rstrip(PADDING)
    return message


class Timer(object):

    def __init__(self):
        self.reset()

    def reset(self):
        self.start = time.time()
        self.finish = None

    def stop(self):
        self.finish = time.time()

    @property
    def elapsed(self):
        t1 = time.time() if self.finish is None else self.finish
        return t1 - self.start

    @property
    def elapsed_str(self):
        delta = datetime.timedelta(seconds=self.elapsed)
        hours = delta.days * 24 + delta.seconds / 3600
        mins = (delta.seconds - hours * 3600) / 60
        secs = (delta.seconds - hours * 3600 - mins * 60)
        mins_secs = "{:02.0f}:{:02.0f}".format(mins, secs)
        return mins_secs if hours == 0 else "{}:{}".format(hours, mins_secs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def __str__(self):
        return self.elapsed_str

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.elapsed)


def doc_inheritor(cls):
    """Apply inherited __doc__ strings to subclass and proxy methods.

        inherits_docs = doc_inheritor(MyBaseClass)

        class MySubClass(MyBaseClass):

            @inherits_docs
            def overwrite_method(self):
                ...

    """
    def inheritor(func):
        if func.__doc__ is None:
            try:
                inherited = getattr(cls, func.__name__)
            except AttributeError:
                pass
            else:
                func.__doc__ = inherited.__doc__
        return func
    return inheritor


class DummyIO(StringIO):

    def write(self, _buffer):
        pass

    def flush(self):
        pass


class LazySequence(object):
    """A sequence which only iterates over its given iterable as needed."""

    REPR_OUTPUT_SIZE = 20

    def __init__(self, iterable=None):
        super(LazySequence, self).__init__()
        self.iterable = iter(iterable) if iterable else None

    @property
    def _results(self):
        return vars(self).setdefault('_results', [])

    def _consume(self):
        if self.iterable:
            self._results.extend(self.iterable)
            self.iterable = None

    def __len__(self):
        self._consume()
        return self._results.__len__()

    def _iter_iterable(self):
        for item in self.iterable or ():
            self._results.append(item)
            yield item
        self.iterable = None

    def __iter__(self):
        if self.iterable:
            return itertools.chain(self._results.__iter__(), self._iter_iterable())
        return self._results.__iter__()

    def __bool__(self):
        try:
            next(iter(self))
        except StopIteration:
            return False
        else:
            return True

    __nonzero__ = __bool__

    def _advance(self, count=None, index=None):
        if count is None and index is None:
            raise TypeError
        elif count is None:
            bound = index + 1
            count = bound - self._results.__len__()

        iterator = self._iter_iterable()
        while count > 0:
            try:
                next(iterator)
            except StopIteration:
                break
            else:
                count -= 1

    @staticmethod
    def _validate_key(key):
        if not isinstance(key, (slice, int)):
            raise TypeError
        elif (
            (not isinstance(key, slice) and key < 0) or
            (isinstance(key, slice) and ((key.start is not None and key.start < 0) or
                                            (key.stop is not None and key.stop < 0)))
        ):
            raise ValueError("Negative indexing is not supported.")

    def __getitem__(self, key):
        self._validate_key(key)

        if isinstance(key, slice):
            return type(self)(itertools.islice(self, key.start, key.stop, key.step))

        if self.iterable:
            self._advance(index=key)
        return self._results.__getitem__(key)

    def __getslice__(self, start, stop):
        return self.__getitem__(slice(start, stop))

    def __repr__(self):
        data = list(self[:self.REPR_OUTPUT_SIZE + 1])
        if len(data) > self.REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return repr(data)

    def count(self, value):
        self._consume()
        return self._results.count(value)

    def index(self, value):
        try:
            return self._results.index(value)
        except ValueError:
            if self.iterable is None:
                raise

            base_length = self._results.__len__()
            for count, item in enumerate(self._iter_iterable()):
                if item == value:
                    return base_length + count
            else:
                raise

    def __contains__(self, value):
        try:
            self.index(value)
        except ValueError:
            return False
        else:
            return True

    def __add__(self, other):
        return type(self)(itertools.chain(self, other))

    def __radd__(self, other):
        return type(other)(itertools.chain(other, self))

    def __mul__(self, other):
        return type(self)(itertools.chain.from_iterable(itertools.repeat(self, other)))

    __rmul__ = __mul__

    def __deepcopy__(self, memo):
        return type(self)(copy.deepcopy(item, memo) for item in self)


class LazyList(LazySequence, list):
    """A list which only iterates over the given iterable as needed."""

    @property
    def _results(self):
        return super(LazySequence, self)

    def __eq__(self, other):
        if self.iterable:
            self._consume()
        try:
            if other.iterable:
                other._consume()
        except AttributeError:
            pass
        return self._results.__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __setitem__(self, key, value):
        self._validate_key(key)

        if self.iterable:
            if isinstance(key, slice):
                stop = sys.maxint if key.stop is None else key.stop
                index = stop - 1
            else:
                index = key
            self._advance(index=index)

        self._results.__setitem__(key, value)

    def __delitem__(self, key):
        self._validate_key(key)

        if self.iterable:
            if isinstance(key, slice):
                stop = sys.maxint if key.stop is None else key.stop
                index = stop - 1
            else:
                index = key
            self._advance(index=index)

        self._results.__delitem__(key)

    def __setslice__(self, start, stop, sequence):
        self.__setitem__(slice(start, stop), sequence)

    def __delslice__(self, start, stop):
        self.__delitem__(slice(start, stop))

    def extend(self, iterable):
        if self.iterable:
            self.iterable = itertools.chain(self.iterable, iterable)
        else:
            self._results.extend(iterable)

    def append(self, value):
        self.extend([value])

    def insert(self, index, value):
        if self.iterable:
            self._advance(index=(index - 1))
        return self._results.insert(index, value)

    def pop(self, index=None):
        if self.iterable:
            if index is None:
                self._consume()
            else:
                self._advance(index=index)
        return self._results.pop(index)

    def remove(self, value):
        index = self.index(value)
        self._results.pop(index)

    def reverse(self):
        self._consume()
        self._results.reverse()

    def sort(self, *args, **kws):
        self._consume()
        self._results.sort(*args, **kws)


class partition(object):
    """An iterator that returns items from `iterable` partitioned into consecutive
    "groups" or "buckets" according to the value range of the items' `key`.

    partition is modeled after groupby and, similarly, expects that the given
    `iterable` is already sorted by `key` and, furthermore, in descending order.

    For example::

        numbers = [85, 70, 50, 40, 40, 25, 3, 2]
        for (lower_bound, group) in partition(numbers, range_width=30, max_value=100):
            print (lower_bound, list(group))

    results in::

        (70, [85, 70])
        (40, [50, 40, 40])
        (10, [25])
        (-20, [3, 2])

    In the above example, the default `key` function, which returns the item itself,
    was used. But, rather than allow the buckets to begin with the first item's value,
    `max_value` was instead set to 100. If we hadn't set `max_value`, the results
    would have been::

        (55, [85, 70])
        (25, [50, 40, 40, 25])
        (-5, [3, 2])

    As opposed to the style of iteration above, the partition iterator may be
    advanced eagerly (without iterating over the partition group at each step);
    however, the partition groups themselves must not be iterated out of order.

    Furthermore, if group iteration is deferred, the partition iterator will
    continue infinitely, unless `min_value` is set, such that the iterator knows
    when its lower bound has decremented sufficiently. For example::

        (bounds, groups) = zip(*partition(numbers, range_width=30, min_value=2))
        for group in groups:
            print list(group)

    results in::

        [85, 70]
        [50, 40, 40, 25]
        [3, 2]

    (Note that `min_value` need not be equal to the minimum key of the iterable;
    but rather, partition may generate superfluous, empty trailing groups in
    satisfying a too-low `min_value`.)

    """
    none = object()

    def __init__(self, iterable, range_width, key=lambda n: n, min_value=None, max_value=None):
        self.iterable = iter(iterable)
        self.range_width = range_width
        self.keyfunc = key
        self.min_value = min_value
        self.lower_bound = max_value
        self.current_item = self.none

    def __iter__(self):
        return self

    def next(self):
        if self.current_item is self.none:
            # Either first loop (don't advance iterable until now) or done;
            # queue up first or raise StopIteration:
            self.current_item = next(self.iterable)
            if self.lower_bound is None:
                self.lower_bound = self.keyfunc(self.current_item)

        if self.lower_bound <= self.min_value:
            # User specified min_value (to support alt generation);
            # last loop already hit:
            raise StopIteration

        self.lower_bound -= self.range_width
        return (self.lower_bound, self._group(self.lower_bound))

    def _group(self, lower_bound):
        while self.keyfunc(self.current_item) >= lower_bound:
            yield self.current_item
            self.current_item = self.none
            # Queue up next or exit at end of iterable:
            self.current_item = next(self.iterable)

partition_edges = functools.partial(partition,
                                    key=lambda edge: edge.score,
                                    min_value=0,
                                    max_value=1)
