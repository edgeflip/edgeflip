from django.db import models

from .manager import assigned


class ChoiceSetFilterQuerySet(assigned.AssignedObjectQuerySet):

    def choose_best_filter(self, edges,
                           use_generic=False,
                           min_friends=2,
                           eligible_proportion=0.5,
                           cache_match=False):
        """Determine the best choice set filter from a list of edges based on
        the filter that passes the largest number of secondaries (average score
        is used for tie breaking)

        use_generic specifies whether the choice set should fall back to friends
          who fall in ANY bin if there not enough friends in a single bin.
        min_friends is the minimum number of friends that must be returned,
          otherwise, we'll raise a TooFewFriendsError.
        eligibleProportion specifies the top fraction (based on score) of friends
          that should even be considered here (if we want to restrict only to
          those friends with a reasonable proximity to the primary).

        """
        sort_func = lambda el: (len(el), sum(e.score for e in el) / len(el) if el else 0)
        edgesSort = sorted(edges, key=lambda x: x.score, reverse=True)
        elgCount = int(len(edges) * eligible_proportion)
        edgesElg = edgesSort[:elgCount]  # only grab the top x% of the pool

        filtered_edges = [
            (csf, csf.filter.filterfeatures.filter_edges(edgesElg, cache_match))
            for csf in self.choicesetfilters.all()
        ]
        sortedFilters = sorted(filtered_edges, key=lambda t: sort_func(t[1]), reverse=True)

        if len(sortedFilters[0][1]) < min_friends:
            if not use_generic:
                raise self.TooFewFriendsError("Too few friends were available after filtering")
            genericFriends = set(e.secondary.fbid for t in sortedFilters for e in t[1])
            if len(genericFriends) < min_friends:
                raise self.TooFewFriendsError("Too few friends were available after filtering")
            return (None, [e for e in edgesElg if e.secondary.fbid in genericFriends])

        return sortedFilters[0]

# TODO: move TooFewFriendsError somewhere reasonable or fix reference
# TODO: fix/clean up above method
# TODO: adjust references to method (currently looking at ChoiceSet)
# TODO: continue work of making perform_filtering use FilterFeatures <= px_rank

class ChoiceSetFilterManager(assigned.AssignedObjectManager):

    def get_query_set(self):
        return ChoiceSetFilterQuerySet.make(self)

    def choose_best_filter(self, *args, **kws):
        return self.get_query_set().choose_best_filter(*args, **kws)


class ChoiceSetFilter(models.Model):

    choice_set_filter_id = models.AutoField(primary_key=True)
    choice_set = models.ForeignKey('ChoiceSet', related_name='choicesetfilters',
                                   null=True, blank=True)
    filter = models.ForeignKey('Filter', null=True, blank=True)
    url_slug = models.CharField(max_length=64, blank=True)
    propensity_model_type = models.CharField(max_length=32, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    objects = ChoiceSetFilterManager.make(assigned_object=filter,
                                          signature_fields=[filter])

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'choice_set_filters'
