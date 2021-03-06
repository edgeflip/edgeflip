import re

import us
from faraday import (
    HashKeyField,
    Item,
    ItemField,
    ItemManager,
    NUMBER,
)
from unidecode import unidecode

from core.utils import names


class cached_class_property(object):
    """Descriptor decorator implementing a class-level property, which replaces
    itself with the static value returned by the method it wraps.

    NOTE: Because this descriptor may replace itself, it does not strictly
    support inheritance. It may be applied without side-effects to the getter
    methods of:

        * classes which do not participate in inheritance
        * abstract classes, (wherein the getter will only be called on children,
        never parents)
        * parent classes which intentionally share this state with their
        children

    """
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        if cls is None:
            cls = type(instance)

        result = self.func(cls)
        setattr(cls, self.func.__name__, result)
        return result


class FeatureMissing(Exception):
    pass


class VoterLookupManager(ItemManager):

    def _make_signature(self, attrs):
        return (self.table.item.hashkey, self.table.item.delimiter.join(attrs))

    def lookup_match(self, obj):
        attrs = self.table.item.extract_attrs(obj)
        missing_features = [
            feature for (feature, value) in zip(self.table.item.keyfeatures, attrs)
            if not value
        ]
        if any(missing_features):
            raise FeatureMissing(missing_features)
        (_hashkey, hashvalue) = self._make_signature(attrs)
        return self.lookup(hashvalue)

    def batch_match(self, objs):
        all_values = (self.table.item.extract_attrs(obj) for obj in objs)
        unique_signatures = {self._make_signature(values) for values in all_values if all(values)}
        return self.batch_get([{hashkey: hashvalue} for (hashkey, hashvalue) in unique_signatures])


def normalize(feature, value):
    if not value:
        return value

    if feature == 'state':
        if len(value) == 2:
            return value.upper()
        state = us.states.lookup(value)
        return state and state.abbr

    if feature == 'lname':
        # First strip any apparent titular suffix
        value = normalize.name_suffix_pttrn.sub('', value)

    decoded = value.decode('utf-8') if isinstance(value, str) else value
    unidecoded = unidecode(decoded)
    return unidecoded.upper().replace(' ', '-')

normalize.name_suffix_pttrn = re.compile(
    # Separator(s) followed by one of these common suffixes:
    r'[, ]+{}$'.format(names.NAME_SUFFIX_PATTERNS),
    # Ignore capitalization:
    re.I
)


class AbstractVoterLookup(Item):

    # MIN scores across all voters who match the concrete signature:
    gotv_score = ItemField(data_type=NUMBER)
    persuasion_score = ItemField(data_type=NUMBER)

    items = VoterLookupManager()

    class Meta(object):
        abstract = True

    # Concrete class's hash key is assumed to be an underscore-delimited combination
    # of voter features, with "state" always first, and "lastname"_"firstname" last.

    delimiter = '_'

    @cached_class_property
    def hashkey(cls):
        return cls.items.table.get_key_fields()[0]

    @cached_class_property
    def keyfeatures(cls):
        return tuple(cls.hashkey.split(cls.delimiter))

    @staticmethod
    def extract_attr(obj, feature):
        attr = getattr(obj, feature, None)
        return normalize(feature, attr)

    @classmethod
    def extract_attrs(cls, obj):
        return tuple(cls.extract_attr(obj, feature) for feature in cls.keyfeatures)

    @classmethod
    def extract_hash(cls, obj):
        attrs = cls.extract_attrs(obj)
        return cls.delimiter.join(attrs)

    @property
    def hashvalue(self):
        return self.pk[0]

    @property
    def attrs(self):
        return tuple(self.hashvalue.split(self.delimiter))

    @property
    def fname(self):
        return self.attrs[-1]

    @property
    def lname(self):
        return self.attrs[-2]

    @property
    def state(self):
        return self.attrs[0]


# Concrete look-up models #

class StateNameVoter(AbstractVoterLookup):

    state_lname_fname = HashKeyField()


class StateCityNameVoter(AbstractVoterLookup):

    state_city_lname_fname = HashKeyField()

    @property
    def city(self):
        return self.attrs[1]


LOOKUPS = (StateCityNameVoter, StateNameVoter)
SUPPORTED_FEATURES = set(AbstractVoterLookup._meta.fields.keys())
