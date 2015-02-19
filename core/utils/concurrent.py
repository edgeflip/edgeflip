"""High-level helpers for the concurrent library."""
from __future__ import absolute_import

import collections
import itertools
import operator
from concurrent import futures


Signature = collections.namedtuple('Signature', ('func', 'args', 'kws'))


def S(func, *args, **kws):
    """Construct a call signature using the call syntax."""
    return Signature(func, args, kws)


EMPTY = S(None)


def _iter_signatures(signatures):
    """Regularize call signatures."""
    for signature in signatures:
        if isinstance(signature, Signature):
            yield signature
            continue

        try:
            withdefaults = itertools.izip_longest(signature, EMPTY)
        except TypeError:
            if not callable(signature):
                raise
            yield S(signature)
        else:
            yield Signature._make((given or default) for (given, default) in withdefaults)


def _parallel(*signatures, **params):
    """Quick-and-dirty parallel function execution using the concurrent.futures
    thread pool.

    Supports the following invocations:

        parallel(myfunc0, myfunc1, ...)
        parallel((myfunc0,), (myfunc1,), ...)
        parallel((myfunc0, (arg0, ...)), ...)
        parallel((myfunc0, (arg0, ...), {key0: ...}), ...)

    and, via helper `S`:

        parallel(S(myfunc0, arg0, key0=value0, ...), ...)

    """
    max_workers = params.get('max_workers', len(signatures))
    timeout = params.get('timeout')
    if len(params) > 2:
        raise TypeError("parallel expected at most 2 keyword argument, got {}".format(len(params)))

    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        fs = {executor.submit(func, *args, **kws): (index, Signature(func, args, kws))
              for (index, (func, args, kws)) in enumerate(_iter_signatures(signatures))}

        for future in futures.as_completed(fs, timeout):
            (index, signature) = fs[future]
            yield (index, signature, future.result())


def parallel_as_completed(*signatures, **kws):
    for (_index, signature, result) in _parallel(*signatures, **kws):
        yield (signature, result)

parallel_as_completed.__doc__ = _parallel.__doc__


def parallel(*signatures, **kws):
    results = sorted(_parallel(*signatures, **kws), key=operator.itemgetter(0))
    return [result for (_index, _signature, result) in results]

parallel.__doc__ = _parallel.__doc__
