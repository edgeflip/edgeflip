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


class Feature(object):
    """Mix-in for models with a "feature" field."""

    class Expression(object):
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

        STANDARD = (
            # (feature type code, feature expression)
            (AGE, AGE),
            (GENDER, GENDER),
            (STATE, STATE),
            (CITY, CITY),
            (FULL_LOCATION, FULL_LOCATION),
        )

        NON_STANDARD = (
            # (feature type code, feature expression)
            (FilterFeatureType.MATCHING, '|'.join([
                TURNOUT_SCORE, SUPPORT_SCORE, PERSUASION_SCORE, GOTV_SCORE, PERSUASION_TURNOUT
            ])),
            (FilterFeatureType.TOPICS, r'topics\[[^\[\]]+\]'),
        )

        ALL = STANDARD + NON_STANDARD

    @staticmethod
    def _format_user_value(value):
        try:
            formatter = value.__feature__
        except AttributeError:
            return value
        else:
            return formatter()

    def get_user_value(self, user):
        """Retrieve from the given User the value corresponding to the feature
        expression.

        Supported expressions are, principally, User attributes; this object may
        then be accessed further via dictionary subscripting:

            * if `feature` is equal to `'age'`, the result of `user.age` is retrieved
            * if `'topics[Health]'`: `user.topics['Health']
            * if `'topics[Health][Exercise]'`: `user.topics['Health']['Exercise']

        Retrieved objects are checked for a `__feature__` method and, if present,
        the result of calling this method is used in place of the object itself;
        (this check is performed at every subscripting level).

        """
        token = r'[^\[\]]+' # string without brackets
        # Expect User attribute followed by optional getitem subscripts:
        result = re.search(r'^({})(.+)?$'.format(token), self.feature)
        if result is None:
            raise ValueError("Unparseable feature expression: {0!r}".format(self.feature))
        (attr, extra) = result.groups()
        if extra is None:
            dive = ()
        else:
            # Parse getitem specifications:
            dive = re.findall(token, extra)
        value = self._format_user_value(getattr(user, attr))
        for level in dive:
            value = self._format_user_value(value[level])
        return value


class FilterFeatureQuerySet(transitory.TransitoryObjectQuerySet):

    def filter_edges(self, edges, cache_match=False):
        """Given a sequence of Edges, return a filtered sequence of those Edges
        for which the secondary passes all queried filter features.

        """
        for filter_feature in self:
            edges = filter_feature.filter_edges(edges, cache_match)
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


class FilterFeature(models.Model, Feature):

    class ValueType(object):
        INT = 'int'
        FLOAT = 'float'
        STRING = 'string'
        LIST = 'list'

        CHOICES = (
            ('', ""),
            (INT, "integer"),
            (FLOAT, "float"),
            (STRING, "string"),
            (LIST, "list"),
        )

        LIST_DELIM = '||'

    class Operator(object):
        IN = 'in'
        EQ = 'eq'
        MIN = 'min'
        MAX = 'max'

        CHOICES = (
            (IN, "In"),
            (EQ, "Equal"),
            (MIN, "Min"),
            (MAX, "Max")
        )

    filter_feature_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter', related_name='filterfeatures', null=True)
    feature = models.CharField(max_length=64, blank=True, validators=[
        get_feature_validator(Feature.Expression.ALL),
    ])
    feature_type = models.ForeignKey('FilterFeatureType')
    operator = models.CharField(max_length=32, blank=True,
                                choices=Operator.CHOICES)
    value = models.CharField(max_length=1024, blank=True)
    value_type = models.CharField(max_length=32, blank=True,
                                  choices=ValueType.CHOICES)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    objects = FilterFeatureManager.make(signature_fields=[feature, operator])

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_features'
        ordering = ('feature_type__sort_order',)

    def decode_value(self):
        ''' Returns the value as the proper value type instance '''
        if self.value_type == self.ValueType.INT:
            return int(self.value)
        elif self.value_type == self.ValueType.FLOAT:
            return float(self.value)
        elif self.value_type == self.ValueType.LIST:
            return self.value.split(self.ValueType.LIST_DELIM)
        else:
            return self.value

    def operate_standard(self, user):
        try:
            user_value = self.get_user_value(user)
        except (AttributeError, KeyError):
            return False
        else:
            if user_value in ('', None):
                return False

        value = self.decode_value()

        if self.operator == self.Operator.MIN:
            return user_value >= value

        elif self.operator == self.Operator.MAX:
            return user_value <= value

        elif self.operator == self.Operator.EQ:
            return user_value == value

        elif self.operator == self.Operator.IN:
            return user_value in value

    def filter_edges(self, edges, cache_match=False):
        if self.feature_type.code == self.feature_type.MATCHING:
            # Civis matching:
            if cache_match:
                filter_ = civis.client.civis_cached_filter
            else:
                filter_ = civis.client.civis_filter

            return filter_(edges, self.feature, self.operator, self.value)

        # Standard min/max/eq/in filters:
        return tuple(edge for edge in edges
                     if self.operate_standard(edge.secondary))

    def determine_value_type(self):
        """Automatically determine value_type from type of value."""
        if isinstance(self.value, (int, long)):
            self.value_type = self.ValueType.INT
        elif isinstance(self.value, float):
            self.value_type = self.ValueType.FLOAT
            self.value = '%.8f' % self.value
        elif isinstance(self.value, basestring):
            self.value_type = self.ValueType.STRING
        elif isinstance(self.value, (list, tuple)):
            self.value_type = self.ValueType.LIST
            self.value = self.ValueType.LIST_DELIM.join(
                str(value) for value in self.value)
        else:
            raise ValueError("Can't filter on type of %s" % self.value)

    def determine_filter_type(self):
        code = self.feature
        for feature_type, pattern in self.Expression.NON_STANDARD:
            if re.search('^{}$'.format(pattern), code):
                code = feature_type
                break
        self.feature_type = FilterFeatureType.objects.get(code=code)

    def save(self, *args, **kws):
        if not self.value_type:
            self.determine_value_type()
        if not self.feature_type_id:
            self.determine_filter_type()
        return super(FilterFeature, self).save(*args, **kws)


class RankingKeyFeatureQuerySet(transitory.TransitoryObjectQuerySet):

    def rank_edges(self, edges):
        edges = list(edges) # Ensure type & don't mutate given object
        # FIXME: You don't necessarily know ordering, so use order_by rather
        # FIXME: than reverse:
        ranking_key_features = self.reverse() # Sort on primary key last, ...
        for ranking_key_feature in ranking_key_features:
            edges.sort(
                key=lambda edge: ranking_key_feature.get_user_value(edge.secondary),
                reverse=ranking_key_feature.reverse,
            )
        return edges


class RankingKeyFeatureManager(transitory.TransitoryObjectManager):

    def get_query_set(self):
        return RankingKeyFeatureQuerySet.make(self)

    def rank_edges(self, *args, **kws):
        return self.get_query_set().rank_edges(*args, **kws)


# TODO: schema migration

class RankingKeyFeature(models.Model, Feature):

    ranking_key_feature_id = models.AutoField(primary_key=True)
    ranking_key = models.ForeignKey('RankingKey', related_name='rankingkeyfeatures', null=True)
    feature = models.CharField(max_length=64, blank=True, validators=[
        validators.RegexValidator(r'^{0[topics]}$'.format(dict(Feature.Expression.ALL)))
    ])
    reverse = models.BooleanField(default=False, blank=True)
    ordinal_position = models.PositiveIntegerField(default=0)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    objects = RankingKeyFeatureManager.make()

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'ranking_key_features'
        ordering = ('ordinal_position',)
        unique_together = ('ranking_key', 'ordinal_position')
