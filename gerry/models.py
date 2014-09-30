import us
from faraday import (
    HashKeyField,
    Item,
    ItemField,
    ItemManager,
    NUMBER,
)


class cached_class_property(object):
    """Descriptor implementing a class-level property, which replaces itself
    with the static value returned by the method it wraps.

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
        return {self.table.item.hashkey: self.table.item.delimiter.join(attrs)}

    def lookup_match(self, obj):
        attrs = self.table.item.extract_attrs(obj)
        missing_features = [
            feature for (feature, value) in zip(self.table.item.keyfeatures, attrs)
            if not value
        ]
        if any(missing_features):
            raise FeatureMissing(missing_features)
        signature = self._make_signature(attrs)
        return self.get_item(**signature)

    def batch_match(self, objs):
        all_values = (self.table.item.extract_attrs(obj) for obj in objs)
        return self.batch_get([self._make_signature(values)
                               for values in all_values if all(values)])


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
    def _extract_attr(obj, feature):
        attr = getattr(obj, feature, None)
        if attr is None:
            return attr

        if feature == 'state':
            if len(attr) == 2:
                return attr.upper()
            state = us.states.lookup(attr)
            return state.abbr

        return attr.upper().replace(' ', '-')

    @classmethod
    def extract_attrs(cls, obj):
        return tuple(cls._extract_attr(obj, feature) for feature in cls.keyfeatures)

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
