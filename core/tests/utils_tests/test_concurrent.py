from nose import tools

from core.utils import concurrent


def doit(*args, **kws):
    return (args, kws)


def test_allowed_interfaces_as_completed():
    def try_interface(signatures, expected):
        [(signature, result)] = list(concurrent.parallel_as_completed(*signatures))
        tools.eq_(signature, expected[0])
        tools.eq_(result, expected[1])

    for (signatures, results) in (
        ([doit],
         ((doit, (), {}), ((), {}))),
        ([(doit,)],
         ((doit, (), {}), ((), {}))),
        ([(doit, (1,))],
         ((doit, (1,), {}), ((1,), {}))),
        ([(doit, (1,), {'a': 'x'})],
         ((doit, (1,), {'a': 'x'}), ((1,), {'a': 'x'}))),
        ([concurrent.S(doit, 1)],
         ((doit, (1,), {}), ((1,), {}))),
        ([concurrent.S(doit, a='x')],
         ((doit, (), {'a': 'x'}), ((), {'a': 'x'}))),
    ):
        yield (try_interface, signatures, results)
