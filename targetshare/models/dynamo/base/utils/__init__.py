import logging
import re
import StringIO

from .. import conf

from .descriptors import cached_property, class_property
from .lazy_sequence import LazySequence, LazyList


LOG = logging.getLogger(conf.settings.LOGGER)


def camel_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class DummyIO(StringIO.StringIO):

    def write(self, _buffer):
        pass

    def flush(self):
        pass

dummyio = DummyIO()


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
