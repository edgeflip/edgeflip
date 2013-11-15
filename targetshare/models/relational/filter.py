import logging

from django.db import models

from targetshare.integration.civis import client


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
        user_val = getattr(user, feature, None)
        if user_val in ('', None):
            return False

        if operator == 'min':
            return user_val >= value

        elif operator == 'max':
            return user_val <= value

        elif operator == 'eq':
            return user_val == value

        elif operator == 'in':
            return user_val in value

    def filter_edges_by_sec(self, edges, cache_match=False):
        """Given a list of edge objects, return those objects for which
        the secondary passes the current filter."""
        for filter_ in self.filterfeatures.all():
            if filter_.feature_type.code == filter_.feature_type.MATCHING:
                # Civis matching:
                if cache_match:
                    edges = client.civis_cached_filter(
                        edges, filter_.feature, filter_.operator, filter_.value
                    )
                else:
                    edges = client.civis_filter(
                        edges, filter_.feature, filter_.operator, filter_.value
                    )
            else:
                # Standard min/max/eq/in filters:
                edges = [edge for edge in edges
                         if self._standard_filter(edge.secondary,
                                                  filter_.feature,
                                                  filter_.operator,
                                                  filter_.decoded_value)]
        return edges

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filters'
        ordering = ('-create_dt',)
