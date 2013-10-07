import logging

from django.db import models

from targetshare import utils


logger = logging.getLogger(__name__)


class Filter(models.Model):

    filter_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', related_name='filters',
                               null=True, blank=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    description = models.CharField(max_length=1024, blank=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def _standard_filter(self, user, feature, operator, value):
        if not hasattr(user, feature):
            return False

        user_val = getattr(user, feature)
        user_val = user_val if user_val else ''

        if operator == 'min':
            return user_val >= value

        elif operator == 'max':
            return user_val <= value

        elif operator == 'eq':
            return user_val == value

        elif operator == 'in':
            return user_val in value

    def filter_edges_by_sec(self, edges):
        """Given a list of edge objects, return those objects for which
        the secondary passes the current filter."""
        if not self.filterfeatures.exists():
            return edges
        for f in self.filterfeatures.all():
            if f.feature_type.code == f.feature_type.MATCHING:
                edges = utils.civis_filter(
                    edges, f.feature, f.operator, f.value
                )
            # Standard min/max/eq/in filters below
            else:
                edges = [x for x in edges if self._standard_filter(
                    x.secondary, f.feature, f.operator, f.value)]
        return edges

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filters'
        ordering = ('-create_dt',)
