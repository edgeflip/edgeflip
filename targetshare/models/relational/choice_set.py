from django.db import models


class ChoiceSet(models.Model):

    choice_set_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client', related_name='choicesets',
                               null=True, blank=True)
    name = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    class TooFewFriendsError(Exception):
        """Too few friends found in picking best choice set filter"""
        pass

    def __unicode__(self):
        return u'%s' % self.name

    def choose_best_filter(self, edges, useGeneric=False,
            minFriends=2, eligibleProportion=0.5, s3_match=False):
        """Determine the best choice set filter from a list of edges based on
        the filter that passes the largest number of secondaries (average score
        is used for tie breaking)

        useGeneric specifies whether the choice set should fall back to friends
          who fall in ANY bin if there not enough friends in a single bin.
        minFriends is the minimum number of friends that must be returned,
          otherwise, we'll raise a TooFewFriendsError.
        eligibleProportion specifies the top fraction (based on score) of friends
          that should even be considered here (if we want to restrict only to
          those friends with a reasonable proximity to the primary).

        """
        sort_func = lambda el: (len(el), sum([e.score for e in el]) / len(el) if el else 0)
        edgesSort = sorted(edges, key=lambda x: x.score, reverse=True)
        elgCount = int(len(edges) * eligibleProportion)
        edgesElg = edgesSort[:elgCount]  # only grab the top x% of the pool

        filtered_edges = [
            (csf, csf.filter.filter_edges_by_sec(
                edgesElg, s3_match)) for csf in self.choicesetfilters.all()
        ]
        sortedFilters = sorted(filtered_edges, key=lambda t: sort_func(t[1]), reverse=True)

        if (len(sortedFilters[0][1]) < minFriends):

            if (not useGeneric):
                raise self.TooFewFriendsError(
                    "Too few friends were available after filtering")

            genericFriends = set(e.secondary.id for t in sortedFilters for e in t[1])
            if (len(genericFriends) < minFriends):
                raise self.TooFewFriendsError(
                    "Too few friends were available after filtering")
            else:
                return (None, [e for e in edgesElg if e.secondary.id in genericFriends])

        return sortedFilters[0]

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'choice_sets'
        ordering = ('-create_dt',)
