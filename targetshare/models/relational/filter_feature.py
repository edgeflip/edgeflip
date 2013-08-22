from django.db import models

from .manager import start_stop_manager


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

    filter_feature_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter', related_name='filterfeatures', null=True)
    feature = models.CharField(max_length=64, blank=True,
                               choices=FEATURE_CHOICES)
    operator = models.CharField(max_length=32, blank=True)
    value = models.CharField(max_length=1024, blank=True)
    value_type = models.CharField(max_length=32, blank=True,
                                  choices=VALUE_TYPE_CHOICES)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    objects = start_stop_manager('feature', 'operator')

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_features'

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

    def save(self, *args, **kws):
        if not self.value_type:
            self.determine_value_type()
        return super(FilterFeature, self).save(*args, **kws)
