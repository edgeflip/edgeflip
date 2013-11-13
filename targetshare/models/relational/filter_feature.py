from django.db import models

from . import manager


class FilterFeatureType(models.Model):

    AGE = 'age'
    GENDER = 'gender'
    STATE = 'state'
    CITY = 'city'
    FULL_LOCATION = 'full_location'
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
    FULL_LOCATION = 'full_location'
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
        (FULL_LOCATION, 'Full Location'),
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

    objects = manager.TransitoryObjectManager.make(
        signature_fields=[feature, operator]
    )

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_features'
        ordering = ('feature_type__sort_order',)

    @property
    def decoded_value(self):
        ''' Returns the value as the proper value type instance '''
        if self.value_type == self.INT:
            return int(self.value)
        elif self.value_type == self.FLOAT:
            return float(self.value)
        elif self.value_type == self.LIST:
            return self.value.split(self.FILTER_LIST_DELIM)
        else:
            return self.value

    def determine_value_type(self):
        """Automatically determine value_type from type of value."""
        if '.' in self.value:
            try:
                self.value = float(self.value)
            except (TypeError, ValueError):
                pass
        else:
            try:
                self.value = long(self.value)
            except (TypeError, ValueError):
                pass

        if isinstance(self.value, (int, long)):
            self.value_type = self.INT
        elif isinstance(self.value, float):
            self.value_type = self.FLOAT
            self.value = '%.8f' % self.value
        elif isinstance(self.value, basestring) and self.FILTER_LIST_DELIM in self.value:
            self.value_type = self.LIST
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
