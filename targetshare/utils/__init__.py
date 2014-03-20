import base64
import datetime
import functools
import logging
import math
import random
import time
import urllib
from Crypto.Cipher import DES

from django.conf import settings
from django.core.urlresolvers import reverse


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


def encodeDES(message, quote=True):
    """Encrypt a message with DES cipher, returning a URL-safe, quoted string"""
    message = str(message)
    encrypted = cipher.encrypt(pad(message))
    b64encoded = base64.urlsafe_b64encode(encrypted)
    if quote:
        return urllib.quote(b64encoded)
    return b64encoded


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


def incoming_redirect(is_secure, host, campaign_id, content_id):
    return urllib.quote_plus('{}{}{}'.format(
        'https://' if is_secure else 'http://',
        host,
        reverse('incoming-encoded', args=[
            encodeDES('%s/%s' % (campaign_id, content_id), quote=False)
        ])
    ))
