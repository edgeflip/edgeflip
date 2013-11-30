import re

from django.core import validators
from django.db import models

from targetshare.integration import civis

from .manager import transitory


class FilterFeatureType(models.Model):

    AGE = 'age'
    GENDER = 'gender'
    STATE = 'state'
    CITY = 'city'
    FULL_LOCATION = 'full_location'
    MATCHING = 'matching'
    TOPICS = 'topics'

    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, unique=True)
    px_rank = models.PositiveIntegerField(default=3)
    sort_order = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'{}'.format(self.name)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_feature_types'
        ordering = ('sort_order',)


class FilterFeatureQuerySet(transitory.TransitoryObjectQuerySet):

    def filter_edges(self, edges, cache_match=False):
        """Given a sequence of Edges, return a filtered sequence of those Edges
        for which the secondary passes all queried filter features.

        """
        for filter_feature in self:
            if filter_feature.feature_type.code == FilterFeatureType.MATCHING:
                # Civis matching:
                edges = filter_feature.filter_matching(edges, cache_match)
            else:
                # Standard min/max/eq/in filters:
                edges = filter_feature.filter_standard(edges)

        return edges


class FilterFeatureManager(transitory.TransitoryObjectManager):

    def get_query_set(self):
        return FilterFeatureQuerySet.make(self)

    def filter_edges(self, *args, **kws):
        return self.get_query_set().filter_edges(*args, **kws)


def get_feature_validator(features):
    return validators.RegexValidator(r'^({COMBINED})$'.format(
        COMBINED='|'.join(pattern for (_feature_type, pattern) in features)
    ))


class FilterFeature(models.Model):

    # value_types:
    INT = 'int'
    FLOAT = 'float'
    STRING = 'string'
    LIST = 'list'

    VALUE_TYPE_CHOICES = (
        ('', ""),
        (INT, "integer"),
        (FLOAT, "float"),
        (STRING, "string"),
        (LIST, "list"),
    )

    FILTER_LIST_DELIM = '||'

    # Standard features:
    AGE = 'age'
    GENDER = 'gender'
    STATE = 'state'
    CITY = 'city'
    FULL_LOCATION = 'full_location'

    # MATCHING features:
    TURNOUT_SCORE = 'turnout_2013'
    SUPPORT_SCORE = 'support_cand_2013'
    PERSUASION_SCORE = 'persuasion_score'
    GOTV_SCORE = 'gotv_score'
    PERSUASION_TURNOUT = 'persuasion_turnout_2013'

    STANDARD_FEATURES = (
        # (feature type code, feature expression)
        (AGE, AGE),
        (GENDER, GENDER),
        (STATE, STATE),
        (CITY, CITY),
        (FULL_LOCATION, FULL_LOCATION),
    )

    NON_STANDARD_FEATURES = (
        # (feature type code, feature expression)
        (FilterFeatureType.MATCHING, '|'.join([
            TURNOUT_SCORE, SUPPORT_SCORE, PERSUASION_SCORE, GOTV_SCORE, PERSUASION_TURNOUT
        ])),
        (FilterFeatureType.TOPICS, r'topics\[[^\[\]]+\]'),
    )

    FEATURES = STANDARD_FEATURES + NON_STANDARD_FEATURES

    OPERATOR_CHOICES = (
        ('in', 'In'),
        ('eq', 'Equal'),
        ('min', 'Min'),
        ('max', 'Max')
    )

    filter_feature_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter', related_name='filterfeatures', null=True)
    feature = models.CharField(max_length=64, blank=True, validators=[
        get_feature_validator(FEATURES),
    ])
    feature_type = models.ForeignKey('FilterFeatureType')
    operator = models.CharField(max_length=32, blank=True,
                                choices=OPERATOR_CHOICES)
    value = models.CharField(max_length=1024, blank=True)
    value_type = models.CharField(max_length=32, blank=True,
                                  choices=VALUE_TYPE_CHOICES)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    objects = FilterFeatureManager.make(signature_fields=[feature, operator])

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_features'
        ordering = ('feature_type__sort_order',)

    def decode_value(self):
        ''' Returns the value as the proper value type instance '''
        if self.value_type == self.INT:
            return int(self.value)
        elif self.value_type == self.FLOAT:
            return float(self.value)
        elif self.value_type == self.LIST:
            return self.value.split(self.FILTER_LIST_DELIM)
        else:
            return self.value

    @staticmethod
    def format_user_value(value):
        try:
            formatter = value.__filterfeature__
        except AttributeError:
            return value
        else:
            return formatter()

    def get_user_value(self, user):
        token = r'[^\[\]]+' # string without brackets
        # Expect User attribute followed by optional getitem specifications:
        result = re.search(r'^({})(.+)?$'.format(token), self.feature)
        if result is None:
            raise ValueError("Unparseable filter feature: {0!r}".format(self.feature))
        (attr, extra) = result.groups()
        if extra is None:
            dive = ()
        else:
            # Parse getitem specifications:
            dive = re.findall(token, extra)
        value = self.format_user_value(getattr(user, attr))
        for level in dive:
            value = self.format_user_value(value[level])
        return value

    def operate_standard(self, user):
        # TODO: Be able to parse topics[Health], and check each object
        # TODO: (first user.topics, then result of __getitem__) for __filterfeature__()
        # TODO: (Or could expect dot notation, though `topics.Health:Cancer` might
        # TODO: look a little weird?)
        try:
            user_val = self.get_user_value(user)
        except (AttributeError, KeyError):
            return False
        else:
            if user_val in ('', None):
                return False

        value = self.decode_value()

        if self.operator == 'min':
            return user_val >= value

        elif self.operator == 'max':
            return user_val <= value

        elif self.operator == 'eq':
            return user_val == value

        elif self.operator == 'in':
            return user_val in value

    def filter_standard(self, edges):
        return tuple(edge for edge in edges
                     if self.operate_standard(edge.secondary))

    def filter_matching(self, edges, cache_match=False):
        if cache_match:
            filter_ = civis.client.civis_cached_filter
        else:
            filter_ = civis.client.civis_filter

        return filter_(edges, self.feature, self.operator, self.value)

    def determine_value_type(self):
        """Automatically determine value_type from type of value."""
        if isinstance(self.value, (int, long)):
            self.value_type = self.INT
        elif isinstance(self.value, float):
            self.value_type = self.FLOAT
            self.value = '%.8f' % self.value
        elif isinstance(self.value, basestring):
            self.value_type = self.STRING
        elif isinstance(self.value, (list, tuple)):
            self.value_type = self.LIST
            self.value = self.FILTER_LIST_DELIM.join(
                str(value) for value in self.value)
        else:
            raise ValueError("Can't filter on type of %s" % self.value)

    def determine_filter_type(self):
        code = self.feature
        for feature_type, pattern in self.NON_STANDARD_FEATURES:
            if re.match(pattern + '$', code):
                code = feature_type
                break
        self.feature_type = FilterFeatureType.objects.get(code=code)

    def save(self, *args, **kws):
        if not self.value_type:
            self.determine_value_type()
        if not self.feature_type_id:
            self.determine_filter_type()
        return super(FilterFeature, self).save(*args, **kws)
