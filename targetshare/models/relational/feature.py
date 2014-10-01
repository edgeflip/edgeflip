import decimal
import itertools
import logging
import numbers
import re
import sys

import gerry
from django.core import validators
from django.db import models

from .manager import transitory, TypeObjectManager


LOG = logging.getLogger('crow')


class FeatureType(models.Model):

    TOPICS = 'topics'

    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = TypeObjectManager()

    def __unicode__(self):
        return u'{}'.format(self.name)

    class Meta(object):
        abstract = True
        app_label = 'targetshare'


class FilterFeatureType(FeatureType):

    AGE = 'age'
    GENDER = 'gender'
    STATE = 'state'
    CITY = 'city'
    FULL_LOCATION = 'full_location'
    CIVIS_VOTER = 'civis_voter'
    EF_VOTER = 'ef_voter'

    px_rank = models.PositiveIntegerField(default=3)
    sort_order = models.IntegerField(default=0)

    class Meta(FeatureType.Meta):
        db_table = 'filter_feature_types'
        ordering = ('sort_order',)


def expressions(*pairs):
    return tuple(
        (code, re.compile('^{}$'.format(pattern)))
        for (code, pattern) in pairs
    )


class Feature(object):
    """Mix-in for models with a "feature" field."""

    class Expression(object):
        # Standard features:
        AGE = 'age'
        GENDER = 'gender'
        STATE = 'state'
        CITY = 'city'
        FULL_LOCATION = 'full_location'

        # Voter matching features:
        TURNOUT_SCORE = 'turnout_2013'
        SUPPORT_SCORE = 'support_cand_2013'
        PERSUASION_SCORE = 'persuasion_score'
        GOTV_SCORE = 'gotv_score'
        PERSUASION_TURNOUT = 'persuasion_turnout_2013'

        STANDARD = expressions(
            # (feature type code, feature expression)
            (AGE, AGE),
            (GENDER, GENDER),
            (STATE, STATE),
            (CITY, CITY),
            (FULL_LOCATION, FULL_LOCATION),
        )

        NON_STANDARD = expressions(
            # (feature type code, feature expression)
            (FilterFeatureType.EF_VOTER, '|'.join([PERSUASION_SCORE, GOTV_SCORE])),
            (FilterFeatureType.CIVIS_VOTER, '|'.join([
                TURNOUT_SCORE, SUPPORT_SCORE, PERSUASION_SCORE, GOTV_SCORE, PERSUASION_TURNOUT
            ])),
            (FilterFeatureType.TOPICS, r'topics\[([^\[\]]+)\]'),
        )

        ALL = dict(STANDARD + NON_STANDARD)

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

    def get_user_value_safe(self, user, default=None):
        try:
            value = self.get_user_value(user)
        except (AttributeError, KeyError, TypeError):
            return default
        else:
            return default if value in ('', None) else value


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
        COMBINED='|'.join(
            feature.pattern.lstrip('^').rstrip('$')
            for feature in features
        )
    ))


class FilterFeature(models.Model, Feature):

    class ValueType(object):
        INT = 'int'
        DECIMAL = 'decimal'
        STRING = 'string'
        LIST = 'list'

        CHOICES = (
            ('', ""),
            (INT, "integer"),
            (DECIMAL, "decimal"),
            (STRING, "string"),
            (LIST, "list"),
        )

        LIST_DELIM = '||'

    class Operator(object):
        BOOL = 'bool'
        BOOL_NOT = 'bool_not'
        EQ = 'eq'
        IN = 'in'
        GT = 'gt'
        LT = 'lt'
        MIN = 'min'
        MAX = 'max'

        CHOICES = (
            (BOOL, "Bool"),
            (BOOL_NOT, "Not"),
            (IN, "In"),
            (EQ, "Equal"),
            (GT, "Greater"),
            (LT, "Lesser"),
            (MIN, "Min"),
            (MAX, "Max")
        )

    filter_feature_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter', related_name='filterfeatures', null=True)
    feature = models.CharField(max_length=64, blank=True, validators=[
        get_feature_validator(Feature.Expression.ALL.values()),
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
        elif self.value_type == self.ValueType.DECIMAL:
            return decimal.Decimal(self.value)
        elif self.value_type == self.ValueType.LIST:
            return self.value.split(self.ValueType.LIST_DELIM)
        else:
            return self.value

    def operate_standard(self, user):
        user_value = self.get_user_value_safe(user)

        # Unary operators (don't depend on FilterFeature.value)

        if self.operator == self.Operator.BOOL:
            return bool(user_value)
        elif self.operator == self.Operator.BOOL_NOT:
            return not user_value

        # Binary operators (depend on FilterFeature.value)

        if user_value is None:
            # User value missing and unsuitable for comparision
            return False

        value = self.decode_value()

        if self.operator == self.Operator.MIN:
            return user_value >= value

        elif self.operator == self.Operator.MAX:
            return user_value <= value

        elif self.operator == self.Operator.GT:
            return user_value > value

        elif self.operator == self.Operator.LT:
            return user_value < value

        elif self.operator == self.Operator.EQ:
            return user_value == value

        elif self.operator == self.Operator.IN:
            return user_value in value

    def filter_edges(self, edges, cache_match=False):
        from targetshare.integration import civis

        if self.feature_type.code == self.feature_type.CIVIS_VOTER:
            # Civis matching:
            if cache_match:
                filter_ = civis.client.civis_cached_filter
            else:
                filter_ = civis.client.civis_filter

            return filter_(edges, self.feature, self.operator, self.value)

        if self.feature_type.code == self.feature_type.EF_VOTER:
            unscored_secondaries = (edge.secondary for edge in edges
                                    if not hasattr(edge.secondary, self.feature))
            # FIXME: Though, through inspection, the above ensures that we
            # don't re-match for the same feature, if for some reason we ever
            # wanted to filter on multiple different voter scores, we'd be
            # matching more than once, unnecessarily.
            first = tuple(itertools.islice(unscored_secondaries, 1))
            if first:
                # Pre-cache relevant feature scores via gerry
                unscored_secondaries = itertools.chain(first, unscored_secondaries)
                gerry.bulk_impute(unscored_secondaries, self.feature)

        # Standard min/max/eq/in filters:
        return [edge for edge in edges if self.operate_standard(edge.secondary)]

    def encode_value(self):
        """Encode value and automatically determine value_type."""
        value = self.value
        if isinstance(value, basestring):
            # Eagerly coerce strings to numbers
            try:
                value = decimal.Decimal(value) if '.' in value else int(value)
            except (decimal.DecimalException, TypeError, ValueError):
                pass

        if isinstance(value, (int, long)):
            return (str(value), self.ValueType.INT)

        if isinstance(value, float):
            return ('%.8f' % value, self.ValueType.DECIMAL)

        if isinstance(value, numbers.Number):
            return (str(value), self.ValueType.DECIMAL)

        if isinstance(value, basestring):
            if self.ValueType.LIST_DELIM in value:
                return (value, self.ValueType.LIST)
            return (value, self.ValueType.STRING)

        if isinstance(value, (list, tuple)):
            value = self.ValueType.LIST_DELIM.join(u'{}'.format(part)
                                                   for part in value)
            return (value, self.ValueType.LIST)

        raise TypeError("Can't filter on type of %s" % self.value)

    def get_feature_type(self):
        code = self.feature
        for (feature_type, pattern) in self.Expression.NON_STANDARD:
            if pattern.search(code):
                code = feature_type
                break
        return FilterFeatureType.objects.get(code=code)

    def save(self, *args, **kws):
        if not self.value_type:
            (self.value, self.value_type) = self.encode_value()
        if not self.feature_type_id:
            self.feature_type = self.get_feature_type()
        return super(FilterFeature, self).save(*args, **kws)

    def __unicode__(self):
        value = self.decode_value()
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        return u'`{feature}` {operator} {value!r}'.format(
            feature=self.feature,
            operator=self.get_operator_display(),
            value=value,
        )


class RankingKeyFeatureQuerySet(transitory.TransitoryObjectQuerySet):

    def sorted_edges(self, edges):
        """Return a sequence of the given Edges sorted according to the
        RankingKeyFeatures of the QuerySet.

        """
        # Ensure type & don't mutate given object:
        edges = list(edges)

        # Sort on primary key last, ...:
        ranking_key_features = self.order_by('-ordinal_position')

        for ranking_key_feature in ranking_key_features:
            null_value = None if ranking_key_feature.reverse else sys.maxint

            def keyfunc(edge):
                return ranking_key_feature.get_user_value_safe(edge.secondary, null_value)
            edges.sort(key=keyfunc, reverse=ranking_key_feature.reverse)

        return edges

    # NOTE: Did we end up using rescored_edges, reranked_edges?
    def rescored_edges(self, edges):
        """Score the given Edges according to the RankingKeyFeatures of the QuerySet.

        RankingKeyFeatures' individual user values are weighted by the order resulting
        from the features' `ordinal_position` -- once normalized to 1, they are
        multiplied by 1, 0.1, 0.01, etc. -- so as to mimic the effect of sorting by
        these keys. These individual scores are then summed and renormalized to 1.

        If `RankingKeyFeature.global_maximum` is set, (and no Edge feature value
        exceeds this value), then this is used to normalize the feature score in
        place of the local maximum value for that feature among the given collection
        of Edges, so as to avoid overweighting of insignificant features; otherwise,
        the local maximum is used.

        If an Edge already has a score, this is combined with the RankingKeyFeatures'
        score, according to the weight given by RankingKey.refinement_weight.
        (`rescored_edges` is intended for use via the RankingKeyFeature
        RelatedManager of an instance of RankingKey.)

        Final scores are normalized to 1.

        """
        ranking_key = getattr(self.manager, 'instance', None)
        if ranking_key is None:
            raise TypeError("rescored_edges is intended for use via RelatedManagers")
        refinement_weight = ranking_key.refinement_weight
        if refinement_weight < 0 or refinement_weight > 1:
            raise ValueError("Unexpected refinement weight (expected 0 <= x <= 1): "
                             "{!r}".format(refinement_weight))
        existing_weight = 1 - refinement_weight
        # In the event of a pre-existing score, rather than allow either the
        # RankingKey score's or the pre-existing score's relative weight to be
        # zero, let it break ties:
        if refinement_weight == 0:
            refinement_weight = 0.1
        elif refinement_weight == 1:
            existing_weight = 0.1
        total_refinement_weight = refinement_weight + existing_weight

        ranking_key_features = self.order_by('ordinal_position')

        # Run through the Edges,
        # keeping a running tally of maximum raw scores, for normalization:
        max_scores = [0] * len(ranking_key_features)
        # and find the maximum pre-existing score (if any):
        existing_max = 0
        # and collect each edge's raw scores:
        edge_scores = []
        for edge in edges:
            raw_scores = tuple(ranking_key_feature.get_user_value_safe(edge.secondary)
                               for ranking_key_feature in ranking_key_features)
            max_scores = [max(max_and_raw) for max_and_raw in zip(raw_scores, max_scores)]
            existing_max = max(existing_max, edge.score)
            edge_scores.append(raw_scores)

        # Compare max scores to expected:
        for (count, ranking_key_feature) in enumerate(ranking_key_features):
            max_score = max_scores[count]
            if ranking_key_feature.global_maximum >= max_score:
                max_scores[count] = ranking_key_feature.global_maximum
            elif ranking_key_feature.global_maximum is not None:
                LOG.error(
                    "Insufficient global maximum for {0!r} ({0.pk}): "
                    "{0.global_maximum!r} < {1!r}"
                    .format(ranking_key_feature, max_score)
                )

        # With tallies made, run through Edges again and apply normalized scores:
        scored_edges = []
        positional_normalization = sum(10 ** -count for count in xrange(len(ranking_key_features)))
        for (edge, raw_scores) in itertools.izip(edges, edge_scores):
            local_score = 0
            for (count, (ranking_key_feature, raw_score, max_score)) in enumerate(
                itertools.izip(ranking_key_features, raw_scores, max_scores)
            ):
                try:
                    # Normalize raw score to 1:
                    feature_score = max_score and float(raw_score) / max_score
                except (ValueError, TypeError):
                    feature_score = 0
                else:
                    if not ranking_key_feature.reverse:
                        # raw scores were really sorting keys already;
                        # 1 is actually the worst score, and vice-versa:
                        feature_score = 1 - feature_score
                # Re-weight score according to ordinal position & add to total:
                positional_weight = 10 ** -count
                local_score += feature_score * positional_weight
            # Normalize aggregate ranking keys' score to 1:
            general_score = local_score / positional_normalization

            if edge.score is None:
                score = general_score
            else:
                # Combine keys' score with pre-existing score according to
                # refinement_weight:
                normalized_existing = existing_max and float(edge.score) / existing_max
                score = (general_score * refinement_weight +
                         normalized_existing * existing_weight) / total_refinement_weight
            scored_edges.append(edge._replace(score=score))
        return scored_edges

    def reranked_edges(self, edges):
        """Return a sequence of the given Edges sorted according to the result of
        `rescored_edges`.

        The given Edges are assumed to be as-yet-unscored or as-yet-unscored by
        RankingKeyFeatures, and as such are passed through `rescored_edges` by this
        method.

        """
        return sorted(self.rescored_edges(edges), key=lambda edge: edge.score, reverse=True)


class RankingKeyFeatureManager(transitory.TransitoryObjectManager):

    def get_query_set(self):
        return RankingKeyFeatureQuerySet.make(self)

    def sorted_edges(self, *args, **kws):
        return self.get_query_set().sorted_edges(*args, **kws)

    def rescored_edges(self, *args, **kws):
        return self.get_query_set().rescored_edges(*args, **kws)

    def reranked_edges(self, *args, **kws):
        return self.get_query_set().reranked_edges(*args, **kws)


class RankingFeatureType(FeatureType):

    class Meta(FeatureType.Meta):
        db_table = 'ranking_feature_types'


class RankingKeyFeature(models.Model, Feature):

    ranking_key_feature_id = models.AutoField(primary_key=True)
    ranking_key = models.ForeignKey('RankingKey', related_name='rankingkeyfeatures', null=True)
    feature = models.CharField(max_length=64, blank=True, validators=[
        validators.RegexValidator(Feature.Expression.ALL['topics'])
    ])
    feature_type = models.ForeignKey('RankingFeatureType')
    # NOTE: Did we end up using global_maximum (reranked_edges, rescored_edges)?
    global_maximum = models.FloatField(blank=True, null=True)
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

    def __unicode__(self):
        return u'{}'.format(self.feature)
