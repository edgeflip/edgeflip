"""jsurls configuration

Lazily constructs jsurls's global settings, wrapping Django's, and defines
setting Profiles.

"""
import collections
import itertools

import django.conf
from django.core.exceptions import ImproperlyConfigured
from django.utils import functional

from jsurls.structs import All


PROFILE_DEFAULTS = (
    ('INSTALL_PATH', None),
    ('JS_NAMESPACE', 'router'),
    ('URL_INCLUDES', ()),
    ('URL_EXCLUDES', ()),
    ('URL_NAMESPACES', ()),
)

GLOBAL_DEFAULTS = PROFILE_DEFAULTS + (
    ('DEBUG_URL', '/jsurls/'),
    ('USE_DEBUG_URL', False),
    ('PROFILES', dict),
)

VALID_SEQUENCES = (collections.Sequence, collections.Set)


def isseq(obj):
    return isinstance(obj, VALID_SEQUENCES)


class AbstractProfile(object):
    """Base class for record and retrieval of a collection of user-specified
    settings -- a "profile" -- which must be outlined by a collection of class-
    level `DEFAULTS`.

    If a user setting was not specified on instantiation, the class-level
    default value is returned on retrieval.

    Between the profile and the class's defaults, a `fallback` object may be
    inserted; if the fallback specifies a setting which the profile does
    not, this is returned on retrieval rather than the class-level default.

        PROFILE > [FALLBACK] > DEFAULTS

    The fallback is assumed, by default, to be "trusted", i.e. to not require
    validation; however, it may be cleaned in the same manner as profile input,
    according to the class-level boolean `CLEANS_FALLBACK`.

    If a class-level default value is callable, its call result is used in place
    of the callable itself.

    Class-level defaults which are sequences or of type `set` dictate that the
    profile setting must also be a sequence or set. (Strings are merely made the
    element of a length-1 container.) On retrieval, the union of the profile's
    setting's values and the default's (or fallback's) is returned.

    Additional cleaning and validation of profile values may be defined as
    methods on the concrete class; to clean a profile class's "verbosity"
    setting, define the method `clean_verbosity()`.

    """
    CLEANS_FALLBACK = False
    DEFAULTS = ()

    @classmethod
    def _generate_defaults(cls):
        for (key, value) in cls.DEFAULTS:
            if callable(value):
                value = value()
            yield (key, value)

    def __init__(self, fallback=None, fallback_prefix='', *args, **kws):
        # Avoid __setattr__
        vars(self)['defaults'] = dict(self._generate_defaults())

        data_input = dict(*args, **kws)
        vars(self).update(
            data=dict(self._clean_input(data_input.iteritems())),
            fallback=fallback,
            fallback_prefix=fallback_prefix,
        )

        if self.CLEANS_FALLBACK and fallback is not None:
            self._clean_fallback()

    def _clean_input(self, stream):
        for (key, value) in stream:
            try:
                default = self.defaults[key]
            except KeyError:
                raise TypeError("Unexpected argument for type {}: {!r}"
                                .format(self.__class__.__name__, key))

            if isseq(default) and not isseq(value):
                raise ImproperlyConfigured("Value {} at key {} is not a valid type"
                                           .format(type(value), key))

            try:
                cleaner = getattr(self, 'clean_' + key.lower())
            except AttributeError:
                pass
            else:
                value = cleaner(value)

            yield (key, value)

    def _fallback_values(self):
        for key in self.defaults:
            try:
                value = getattr(self.fallback, self.fallback_prefix + key)
            except AttributeError:
                pass
            else:
                yield (key, value)

    def _clean_fallback(self):
        for (key, value) in self._clean_input(self._fallback_values()):
            setattr(self.fallback, self.fallback_prefix + key, value)

    def __getattr__(self, key):
        try:
            default = self.defaults[key]
        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'"
                                .format(self.__class__.__name__, key))

        if self.fallback is None:
            fallback_value = default
        else:
            fallback_value = getattr(self.fallback, self.fallback_prefix + key, default)

        if isinstance(default, basestring) or not isseq(default):
            return self.data.get(key, fallback_value)

        # Chain profile value and fallback:
        set_value = self.data.get(key, ())
        values = [(value,) if isinstance(value, basestring) else value
                  for value in (fallback_value, set_value)]

        if any(value is All for value in values):
            return All

        return frozenset(itertools.chain.from_iterable(values))

    def __setattr__(self, key, value):
        if key in self.defaults:
            self.data[key] = value
        else:
            super(AbstractProfile, self).__setattr__(key, value)


class Profile(AbstractProfile):

    DEFAULTS = PROFILE_DEFAULTS

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(self.__class__.__name__,
                                             self.fallback,
                                             self.fallback_prefix,
                                             self.data)


class GlobalSettings(AbstractProfile):

    CLEANS_FALLBACK = True
    DEFAULTS = GLOBAL_DEFAULTS

    @classmethod
    def lazy(cls):
        return functional.lazy(cls.read, cls)(django.conf.settings)

    @classmethod
    def read(cls, fallback, fallback_prefix='JSURLS_'):
        return cls(fallback, fallback_prefix)

    def __repr__(self):
        return "<{}.{}>".format(self.__module__, self.__class__.__name__)

    def clean_profiles(self, value):
        if not isinstance(value, dict):
            raise ImproperlyConfigured("{}PROFILES must be a dict".format(self.fallback_prefix))

        for (profile_name, profile) in value.items():
            if isinstance(profile, dict):
                value[profile_name] = Profile(self, '', profile)
            elif isinstance(profile, Profile):
                profile.fallback = self
            else:
                raise ImproperlyConfigured("{}PROFILES values must be dicts or Profiles"
                                           .format(self.fallback_prefix))

        return value

settings = GlobalSettings.lazy()
