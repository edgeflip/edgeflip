from django.db import models

from .manager import assigned


class ChoiceSetFilterQuerySet(assigned.AssignedObjectQuerySet):

    def choose_best_filter(self, edges,
                           use_generic=False,
                           min_friends=2,
                           eligible_proportion=1.0,
                           cache_match=False):
        """Determine the best choice set filter for a sequence of edges, based on
        the filter that returns the largest number of secondaries, (where the
        average of their proximity scores is used for tie breaking).

        Parameters:

            use_generic: specifies whether the choice set should fall back to friends
                who fall in ANY bin if there not enough friends in a single bin
            min_friends: is the minimum number of friends that must be returned;
                otherwise, we'll raise a TooFewFriendsError
            eligible_proportion: specifies the top fraction (based on score) of friends
                that should even be considered here (if we want to restrict only to
                those friends with a reasonable proximity to the primary)

        """
        edges = sorted(edges, key=lambda edge: edge.score, reverse=True)
        eligible_count = int(len(edges) * eligible_proportion)
        edges_eligible = edges[:eligible_count] # only grab the top x% of the pool

        def filter_sort(element):
            (_filter, filtered) = element
            key0 = len(filtered)
            key1 = key0 and sum(edge.score for edge in filtered) / key0
            return (key0, key1)
        filter_filtered = (
            (csf, csf.filter.filterfeatures.filter_edges(edges_eligible, cache_match))
            for csf in self
        )
        filter_filtered = sorted(filter_filtered, key=filter_sort, reverse=True)

        (best_filter, best_filtered) = filter_filtered[0]
        if len(best_filtered) < min_friends:
            if use_generic:
                generic_friends = {edge.secondary.fbid
                                   for (_filter, edges) in filter_filtered
                                   for edge in edges}
                if len(generic_friends) >= min_friends:
                    return (None, tuple(edge for edge in edges_eligible
                                        if edge.secondary.fbid in generic_friends))
            raise self.model.TooFewFriendsError("Too few friends were available "
                                                "after filtering")

        return (best_filter, best_filtered)


class ChoiceSetFilterManager(assigned.AssignedObjectManager):

    def get_query_set(self):
        return ChoiceSetFilterQuerySet.make(self)

    def choose_best_filter(self, *args, **kws):
        return self.get_query_set().choose_best_filter(*args, **kws)


class ChoiceSetFilter(models.Model):

    choice_set_filter_id = models.AutoField(primary_key=True)
    choice_set = models.ForeignKey('ChoiceSet', related_name='choicesetfilters',
                                   null=True, blank=True)
    filter = models.ForeignKey('Filter', null=True, blank=True,
                               related_name='choicesetfilters')
    url_slug = models.CharField(max_length=64, blank=True)
    propensity_model_type = models.CharField(max_length=32, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    objects = ChoiceSetFilterManager.make(assigned_object=filter,
                                          signature_fields=[filter])

    class TooFewFriendsError(Exception):
        """Too few friends found in picking best choice set filter"""

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'choice_set_filters'
