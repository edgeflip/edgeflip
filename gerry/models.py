from faraday import (
    Item,
    ItemField,
    ItemManager,
    HashKeyField,
    NUMBER,
)


class cached_class_property(object):

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

    def _make_signature(self, values):
        return {self.table.item.hashkey: self.table.item.delimiter.join(values)}

    def lookup_match(self, voter):
        voter_attrs = self.table.item.extract_attrs(voter)
        missing_features = [feature for (feature, value) in voter_attrs if not value]
        if any(missing_features):
            raise FeatureMissing(missing_features)
        signature = self._make_signature(value for (_feature, value) in voter_attrs)
        return self.get_item(**signature)

    def batch_match(self, voters):
        all_values = (
            [value for (_feature, value) in self.table.item.extract_attrs(voter)]
            for voter in voters
        )
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
        for (name, field) in cls._meta.keys.items():
            if isinstance(field, HashKeyField):
                return name

    @cached_class_property
    def features(cls):
        return cls.hashkey.split(cls.delimiter)

    @classmethod
    def extract_attrs(cls, obj):
        return [(feature, getattr(obj, feature)) for feature in cls.features]

    @property
    def hashvalue(self):
        return self.pk[0]

    @property
    def attrs(self):
        return self.hashvalue.split(self.delimiter)

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
