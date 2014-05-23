import collections


class _All(object):
    pass

collections.Sequence.register(_All)

All = _All()
