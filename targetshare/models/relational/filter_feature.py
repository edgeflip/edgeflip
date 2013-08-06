from django.db import models

from .manager import StartStopManager


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

    filter_feature_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter')
    feature = models.CharField(max_length=64)
    operator = models.CharField(max_length=32)
    value = models.CharField(max_length=1024)
    value_type = models.CharField(max_length=32, choices=VALUE_TYPE_CHOICES)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    objects = StartStopManager()

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filter_features'
        ss_fields = ('feature', 'operator')

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
