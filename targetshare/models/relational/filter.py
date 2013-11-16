import logging

from django.db import models


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

    def filter_edges_by_sec(self, edges, cache_match=False):
        """Given a list of edge objects, return those objects for which
        the secondary passes the current filter."""
        for filter_ in self.filterfeatures.all():
            if filter_.feature_type.code == filter_.feature_type.MATCHING:
                # Civis matching:
                edges = filter_.filter_matching(edges, cache_match)
            else:
                # Standard min/max/eq/in filters:
                edges = filter_.filter_standard(edges)
        return edges

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'filters'
        ordering = ('-create_dt',)
