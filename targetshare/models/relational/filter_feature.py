from django.db import models

from .manager import start_stop_manager


class FilterFeatureType(models.Model):

    AGE = 'age'
    GENDER = 'gender'
    STATE = 'state'
    CITY = 'city'
    MATCHING = 'matching'

    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, unique=True)
    sort_order = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'{}'.format(self.name)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_feature_types'
        ordering = ('sort_order',)


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

    AGE = 'age'
    GENDER = 'gender'
    STATE = 'state'
    CITY = 'city'
    TURNOUT_SCORE = 'turnout_2013'
    SUPPORT_SCORE = 'support_cand_2013'
    PERSUASION_SCORE = 'persuasion_score'
    GOTV_SCORE = 'gotv_score'
    PERSUASION_TURNOUT = 'persuasion_turnout_2013'

    CIVIS_FEATURES = (
        TURNOUT_SCORE, SUPPORT_SCORE, PERSUASION_SCORE, GOTV_SCORE,
        PERSUASION_TURNOUT
    )

    FEATURE_CHOICES = (
        (AGE, 'Age'),
        (GENDER, 'Gender'),
        (STATE, 'State'),
        (CITY, 'City'),
        (TURNOUT_SCORE, 'Turnout Score'),
        (PERSUASION_SCORE, 'Persuasion Score'),
        (GOTV_SCORE, 'GOTV Score'),
        (PERSUASION_TURNOUT, 'Persuasion x Turnout Score')
    )

    OPERATOR_CHOICES = (
        ('in', 'In'),
        ('eq', 'Equal'),
        ('min', 'Min'),
        ('max', 'Max')
    )

    filter_feature_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter', related_name='filterfeatures', null=True)
    feature = models.CharField(max_length=64, blank=True,
                               choices=FEATURE_CHOICES)
    feature_type = models.ForeignKey('FilterFeatureType')
    operator = models.CharField(max_length=32, blank=True,
                                choices=OPERATOR_CHOICES)
    value = models.CharField(max_length=1024, blank=True)
    value_type = models.CharField(max_length=32, blank=True,
                                  choices=VALUE_TYPE_CHOICES)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    objects = start_stop_manager('feature', 'operator')

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_features'
        ordering = ('feature_type__sort_order',)

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
        if self.feature in self.CIVIS_FEATURES:
            self.feature_type = FilterFeatureType.objects.get(
                code=FilterFeatureType.MATCHING)
        else:
            self.feature_type = FilterFeatureType.objects.get(
                code=self.feature)

    def save(self, *args, **kws):
        if not self.value_type:
            self.determine_value_type()
        if not self.feature_type_id:
            self.determine_filter_type()
        return super(FilterFeature, self).save(*args, **kws)
