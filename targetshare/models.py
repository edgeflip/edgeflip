import time
import logging
import datetime
import threading

from django.db import models
from django.conf import settings

from targetshare import datastructs, utils

logger = logging.getLogger(__name__)


class Assignment(models.Model):

    assignment_id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=128)
    campaign = models.ForeignKey('Campaign')
    content = models.ForeignKey('ClientContent')
    feature_type = models.CharField(max_length=128)
    feature_row = models.IntegerField()
    random_assign = models.BooleanField(default=False)
    assign_dt = models.DateTimeField(auto_now_add=True)
    chosen_from_table = models.CharField(max_length=128)
    chosen_from_rows = models.CharField(max_length=128)

    class Meta:
        db_table = 'assignments'


class Client(models.Model):

    client_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    fb_app_name = models.CharField(max_length=256)
    fb_app_id = models.CharField(max_length=256)
    domain = models.CharField(max_length=256)
    subdomain = models.CharField(max_length=256)
    create_dt = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'clients'


class Campaign(models.Model):

    campaign_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client')
    name = models.CharField(max_length=256)
    description = models.TextField(null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'campaigns'


class ButtonStyle(models.Model):

    button_style_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client')
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'button_styles'


class ButtonStyleFile(models.Model):

    button_style_file_id = models.AutoField(primary_key=True)
    button_style = models.ForeignKey('ButtonStyle')
    html_template = models.CharField(max_length=256, null=True)
    css_file = models.CharField(max_length=256, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'button_style_files'


class ButtonStyleMeta(models.Model):

    button_style_meta_id = models.AutoField(primary_key=True)
    button_style = models.ForeignKey('ButtonStyle')
    name = models.CharField(max_length=256)
    value = models.TextField(blank=True, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'button_style_meta'


class CampaignButtonStyle(models.Model):

    campaign_button_style_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    button_style = models.ForeignKey('ButtonStyle')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_button_styles'


class ChoiceSet(models.Model):

    choice_set_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client')
    name = models.CharField(max_length=256)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    def choose_best_filter(self, edges, useGeneric=False,
            minFriends=2, eligibleProportion=0.5):
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
                edgesElg)) for csf in self.choicesetfilter_set.all()
        ]
        sortedFilters = sorted(filtered_edges, key=lambda t: sort_func(t[1]), reverse=True)

        if (len(sortedFilters[0][1]) < minFriends):

            if (not useGeneric):
                raise utils.TooFewFriendsError(
                    "Too few friends were available after filtering")

            genericFriends = set(e.secondary.id for t in sortedFilters for e in t[1])
            if (len(genericFriends) < minFriends):
                raise utils.TooFewFriendsError(
                    "Too few friends were available after filtering")
            else:
                return (None, [e for e in edgesElg if e.secondary.id in genericFriends])

        return sortedFilters[0]

    class Meta:
        db_table = 'choice_sets'


class ChoiceSetAlgorithm(models.Model):

    choice_set_algorithm_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True)
    description = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'choice_set_algoritms'


class CampaignChoiceSetAlgorithm(models.Model):

    campaign_choice_set_algoritm_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    choice_set_algorithm = models.ForeignKey(
        'ChoiceSetAlgorithm',
        db_column='choice_set_algoritm_id'
    )
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_choice_set_algoritm'


class CampaignChoiceSet(models.Model):

    campaign_choice_set_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    choice_set = models.ForeignKey('ChoiceSet')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    allow_generic = models.NullBooleanField()
    generic_url_slug = models.CharField(max_length=64, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_choice_sets'


class CampaignFacesStyle(models.Model):

    campaign_faces_style_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    faces_style = models.ForeignKey('FacesStyle')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_faces_styles'


class CampaignFBObjects(models.Model):

    campaign_fb_object_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    filter = models.ForeignKey('Filter')
    fb_object = models.ForeignKey('FBObject')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_fb_objects'


class CampaignGenericFBObjects(models.Model):

    campaign_generic_fb_object_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    fb_object = models.ForeignKey('FBObject')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_generic_fb_objects'


class CampaignGlobalFilter(models.Model):

    campaign_global_filter_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    filter = models.ForeignKey('Filter')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_global_filters'


class CampaignMeta(models.Model):

    campaign_meta_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    name = models.CharField(max_length=256)
    value = models.TextField(blank=True, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'campaign_meta'


class CampaignMixModel(models.Model):

    campaign_mix_model_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    mix_model = models.ForeignKey('MixModel')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_mix_models'


class CampaignPropensityModel(models.Model):

    campaign_propensity_model_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    propensity_model = models.ForeignKey('PropensityModel')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_propensity_models'


class CampaignProperties(models.Model):

    campaign_property_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    client_faces_url = models.CharField(max_length=2096)
    client_thanks_url = models.CharField(max_length=2096)
    client_error_url = models.CharField(max_length=2096)
    fallback_campaign = models.ForeignKey(
        'Campaign',
        related_name='fallback_campaign',
        null=True
    )
    fallback_content = models.ForeignKey('ClientContent', null=True)
    fallback_is_cascading = models.NullBooleanField()
    min_friends = models.IntegerField(default=1)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def faces_url(self, content_id):
        url = self.client_faces_url
        if (url.find('?') == -1):
            url += '?'
        else:
            url += '&'

        slug = utils.encodeDES('%s/%s' % (self.campaign_id, content_id))

        return url + 'efcmpgslug=' + str(slug)

    class Meta:
        db_table = 'campaign_properties'


class CampaignProximityModel(models.Model):

    campaign_proximity_model_id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey('Campaign')
    proximity_model = models.ForeignKey('ProximityModel')
    rand_cdf = models.DecimalField(max_digits=10, decimal_places=9)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'campaign_proximity_models'


class ChoiceSetAlgorithmDefinition(models.Model):

    choice_set_algorithm_definition_id = models.AutoField(
        db_column='choice_set_algoritm_definition_id',
        primary_key=True
    )
    choice_set_algorithm = models.ForeignKey(
        'ChoiceSetAlgorithm',
        db_column='choice_set_algoritm_id'
    )
    algorithm_definition = models.TextField(null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'choice_set_algoritm_definitions'


class ChoiceSetAlgorithmMeta(models.Model):

    choice_set_algorithm_meta_id = models.AutoField(
        db_column='choice_set_algoritm_meta_id',
        primary_key=True
    )
    choice_set_algorithm = models.ForeignKey(
        'ChoiceSetAlgorithm',
        db_column='choice_set_algoritm_id'
    )
    name = models.CharField(max_length=256, null=True)
    value = models.CharField(max_length=1024, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'choice_set_algoritm_meta'


class ChoiceSetFilter(models.Model):

    choice_set_filter_id = models.AutoField(primary_key=True)
    choice_set = models.ForeignKey('ChoiceSet')
    filter = models.ForeignKey('Filter')
    url_slug = models.CharField(max_length=64)
    propensity_model_type = models.CharField(max_length=32, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'choice_set_filters'


class ChoiceSetMeta(models.Model):

    choice_set_meta_id = models.AutoField(primary_key=True)
    choice_set = models.ForeignKey('ChoiceSet')
    name = models.CharField(max_length=256, null=True)
    value = models.CharField(max_length=1024, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'choice_set_meta'


class ClientContent(models.Model):

    content_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client')
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=1024, null=True)
    url = models.CharField(max_length=2048, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'client_content'


class ClientDefault(models.Model):

    client_default_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client')
    button_style = models.ForeignKey('ButtonStyle', null=True)
    faces_style = models.ForeignKey('FacesStyle', null=True)
    propensity_model = models.ForeignKey('PropensityModel', null=True)
    proximity_model = models.ForeignKey('ProximityModel', null=True)
    mix_model = models.ForeignKey('MixModel', null=True)
    filter = models.ForeignKey('Filter', null=True)
    choice_set = models.ForeignKey('ChoiceSet', null=True)
    choice_set_algorithm = models.ForeignKey('ChoiceSetAlgorithm', null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'client_defaults'


class Edge(models.Model):

    edge_id = models.AutoField(primary_key=True)
    fbid_source = models.BigIntegerField()
    fbid_target = models.BigIntegerField()
    post_likes = models.IntegerField(null=True)
    post_comms = models.IntegerField(null=True)
    stat_likes = models.IntegerField(null=True)
    stat_comms = models.IntegerField(null=True)
    wall_posts = models.IntegerField(null=True)
    wall_comms = models.IntegerField(null=True)
    tags = models.IntegerField(null=True)
    photos_target = models.IntegerField(null=True)
    photos_other = models.IntegerField(null=True)
    mut_friends = models.IntegerField(null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('fbid_source', 'fbid_target')
        db_table = 'edges'


class Event(models.Model):

    event_id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=128)
    campaign = models.ForeignKey('Campaign', null=True)
    client_content = models.ForeignKey(
        'ClientContent',
        db_column='content_id',
        null=True
    )
    ip = models.CharField(max_length=32)
    fbid = models.BigIntegerField(null=True)
    friend_fbid = models.BigIntegerField(null=True)
    event_type = models.CharField(max_length=64, db_column='type')
    app_id = models.BigIntegerField(db_column='appid')
    content = models.CharField(max_length=128)
    activity_id = models.BigIntegerField(null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            'session_id', 'campaign', 'content',
            'fbid', 'friend_fbid', 'activity_id'
        )
        db_table = 'events'


class FaceExclusion(models.Model):

    face_exclusion_id = models.AutoField(primary_key=True)
    fbid = models.BigIntegerField()
    campaign = models.ForeignKey('Campaign')
    content = models.ForeignKey('ClientContent')
    friend_fbid = models.BigIntegerField()
    reason = models.CharField(max_length=512, null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('fbid', 'campaign', 'content', 'friend_fbid')
        db_table = 'face_exclusions'


class FacesStyle(models.Model):

    faces_style_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client')
    name = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'faces_styles'


class FacesStyleFiles(models.Model):

    faces_style_file_id = models.AutoField(primary_key=True)
    faces_style = models.ForeignKey('FacesStyle')
    html_template = models.CharField(max_length=128)
    css_file = models.CharField(max_length=128)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'faces_style_files'


class FacesStyleMeta(models.Model):

    faces_style_meta_id = models.AutoField(primary_key=True)
    faces_style = models.ForeignKey('FacesStyle')
    name = models.CharField(max_length=128)
    value = models.CharField(max_length=1024)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'faces_style_meta'


class FBObjectAttribute(models.Model):

    fb_object_attributes_id = models.AutoField(primary_key=True)
    fb_object = models.ForeignKey('FBObject')
    og_action = models.CharField(max_length=64, null=True)
    og_type = models.CharField(max_length=64, null=True)
    og_title = models.CharField(max_length=128, null=True)
    og_image = models.CharField(max_length=2096, null=True)
    og_description = models.CharField(max_length=1024, null=True)
    page_title = models.CharField(max_length=256, null=True)
    sharing_prompt = models.CharField(max_length=2096, null=True)
    msg1_pre = models.CharField(max_length=1024, null=True)
    msg1_post = models.CharField(max_length=1024, null=True)
    msg2_pre = models.CharField(max_length=1024, null=True)
    msg2_post = models.CharField(max_length=1024, null=True)
    url_slug = models.CharField(max_length=64, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'fb_object_attributes'


class FBObjectMeta(models.Model):

    fb_object_meta_id = models.AutoField(primary_key=True)
    fb_object = models.ForeignKey('FBObject')
    name = models.CharField(max_length=128)
    value = models.CharField(max_length=1024)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'fb_object_meta'


class FBObject(models.Model):

    fb_object_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client')
    name = models.CharField(max_length=256, null=True)
    description = models.CharField(max_length=1024, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'fb_objects'


class FilterFeature(models.Model):

    filter_feature_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter')
    feature = models.CharField(max_length=64)
    operator = models.CharField(max_length=32)
    value = models.CharField(max_length=1024)
    value_type = models.CharField(max_length=32)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'filter_features'


class FilterMeta(models.Model):

    filter_meta_id = models.AutoField(primary_key=True)
    filter = models.ForeignKey('Filter')
    name = models.CharField(max_length=128)
    value = models.CharField(max_length=1024)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'filter_meta'


class Filter(models.Model):

    filter_id = models.AutoField(primary_key=True)
    client = models.ForeignKey('Client')
    name = models.CharField(max_length=256, null=True)
    description = models.CharField(max_length=1024, null=True)
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
        if not self.filterfeature_set.exists():
            return edges
        for f in self.filterfeature_set.all():
            if f.feature in settings.CIVIS_FILTERS:
                start_time = time.time()
                threads = []
                loopTimeout = 10
                loopSleep = 0.1
                matches = []
                for count, edge in enumerate(edges):
                    t = threading.Thread(
                        target=utils.civis_filter,
                        args=(edge, f.feature, f.operator, f.value, matches)
                    )
                    t.setDaemon(True)
                    t.name = 'civis-%d' % count
                    threads.append(t)
                    t.start()

                timeStop = time.time() + loopTimeout
                while (time.time() < timeStop):
                    threadsAlive = []
                    for t in threads:
                        if t.isAlive():
                            threadsAlive.append(t)

                    threads = threadsAlive
                    if (threadsAlive):
                        time.sleep(loopSleep)
                    else:
                        break
                logger.debug(
                    "Civis matching complete in %s" % (time.time() - start_time)
                )
                edges = [
                    x for x in matches if isinstance(x, datastructs.Edge)
                ]

            # Standard min/max/eq/in filters below
            else:
                edges = [x for x in edges if self._standard_filter(
                    x.secondary, f.feature, f.operator, f.value)]
        return edges

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'filters'


class MixModelDefinition(models.Model):

    mix_model_definition_id = models.AutoField(primary_key=True)
    mix_model = models.ForeignKey('MixModel')
    model_definition = models.TextField(null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'mix_model_definitions'


class MixModelMeta(models.Model):

    mix_model_meta_id = models.AutoField(primary_key=True)
    mix_model = models.ForeignKey('MixModel')
    name = models.CharField(max_length=256, null=True)
    value = models.CharField(max_length=1024, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'mix_model_meta'


class MixModel(models.Model):

    mix_model_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True)
    description = models.CharField(max_length=1024, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'mix_models'


class PropensityModelDefinition(models.Model):

    propensity_model_definition_id = models.AutoField(primary_key=True)
    propensity_model = models.ForeignKey('PropensityModel')
    propensity_model_type = models.CharField(max_length=64, null=True)
    model_definition = models.TextField(null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'propensity_model_definitions'


class PropensityModelMeta(models.Model):

    propensity_model_meta_id = models.AutoField(primary_key=True)
    propensity_model = models.ForeignKey('PropensityModel')
    name = models.CharField(max_length=256, null=True)
    value = models.CharField(max_length=1024, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'propensity_model_meta'


class PropensityModel(models.Model):

    proximity_model_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True)
    description = models.CharField(max_length=1024, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'propensity_models'


class ProximityModelDefinition(models.Model):

    proximity_model_definition_id = models.AutoField(primary_key=True)
    proximity_model = models.ForeignKey('ProximityModel')
    model_definition = models.TextField(null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'proximity_model_definitions'


class ProximityModelMeta(models.Model):

    proximity_model_meta_id = models.AutoField(primary_key=True)
    proximity_model = models.ForeignKey('ProximityModel')
    name = models.CharField(max_length=256, null=True)
    value = models.CharField(max_length=1024, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'proximity_model_meta'


class ProximityModel(models.Model):

    proximity_model_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True)
    description = models.CharField(max_length=1024, null=True)
    is_deleted = models.BooleanField(default=False)
    create_dt = models.DateTimeField(auto_now_add=True)
    delete_dt = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        db_table = 'proximity_models'


class ShareMessage(models.Model):

    activity_id = models.BigIntegerField(primary_key=True, default=0)
    fbid = models.BigIntegerField()
    campaign = models.ForeignKey('Campaign')
    content = models.ForeignKey('ClientContent')
    message = models.TextField(null=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'share_messages'


class Token(models.Model):

    fbid = models.BigIntegerField(primary_key=True)
    app_id = models.BigIntegerField(db_column='appid')
    owner_id = models.BigIntegerField(db_column='ownerid')
    token = models.CharField(max_length=512)
    expires = models.DateTimeField(null=True)
    updated = models.DateTimeField(auto_now=True, default=datetime.datetime.now)

    class Meta:
        unique_together = ('fbid', 'app_id', 'owner_id')
        db_table = 'tokens'


class UserClient(models.Model):

    user_client_id = models.AutoField(primary_key=True)
    fbid = models.BigIntegerField()
    client = models.ForeignKey('Client')
    create_dt = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('fbid', 'client')
        db_table = 'user_clients'


class User(models.Model):

    fbid = models.BigIntegerField(primary_key=True)
    first_name = models.CharField(max_length=128, null=True, db_column='fname')
    last_name = models.CharField(max_length=128, null=True, db_column='lname')
    email = models.CharField(max_length=256, null=True)
    gender = models.CharField(max_length=8, null=True)
    birthday = models.DateTimeField(null=True)
    city = models.CharField(max_length=32, null=True)
    state = models.CharField(max_length=32, null=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s %s' % (self.first_name, self.last_name)

    class Meta:
        db_table = 'users'
