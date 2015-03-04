import abc
import functools


class ViewDecorator(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, view):
        functools.update_wrapper(self, view)
        self._view = view

    @abc.abstractmethod
    def __call__(self, request, *args, **kws):
        raise NotImplementedError
