import base64
import copy
import datetime
import itertools
import logging
import random
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
    """used for inline profiling & debugging


    XXX i can probably die
    """
    def __init__(self):
        self.start = time.time()

    def reset(self):
        self.start = time.time()

    def elapsedSecs(self):
        return time.time() - self.start

    def elapsedPr(self, precision=2):
        delt = datetime.timedelta(seconds=time.time() - self.start)
        hours = delt.days * 24 + delt.seconds / 3600
        hoursStr = str(hours)
        mins = (delt.seconds - hours * 3600) / 60
        minsStr = "%02d" % (mins)
        secs = (delt.seconds - hours * 3600 - mins * 60)
        if (precision):
            secsFloat = secs + delt.microseconds / 1000000.0 # e.g., 2.345678
            secsStr = (("%." + str(precision) + "f") % (secsFloat)).zfill(3 + precision) # two digits, dot, fracs
        else:
            secsStr = "%02d" % (secs)
        if (hours == 0):
            return minsStr + ":" + secsStr
        else:
            return hoursStr + ":" + minsStr + ":" + secsStr

    def stderr(self, txt=""):
        raise NotImplementedError # what is this intended to do? No stderr please!


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
