# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Assignment'
        db.create_table('assignments', (
            ('session_id', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ClientContent'])),
            ('feature_type', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('feature_row', self.gf('django.db.models.fields.IntegerField')()),
            ('random_assign', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('assign_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('chosen_from_table', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('chosen_from_rows', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal(u'targetshare', ['Assignment'])

        # Adding model 'Client'
        db.create_table('clients', (
            ('client_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('fb_app_name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('fb_app_id', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('subdomain', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['Client'])

        # Adding model 'Campaign'
        db.create_table('campaigns', (
            ('campaign_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['Campaign'])

        # Adding model 'ButtonStyle'
        db.create_table('button_styles', (
            ('button_style_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ButtonStyle'])

        # Adding model 'ButtonStyleFile'
        db.create_table('button_style_files', (
            ('button_style_file_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('button_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ButtonStyle'])),
            ('html_template', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('css_file', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ButtonStyleFile'])

        # Adding model 'ButtonStyleMeta'
        db.create_table('button_style_meta', (
            ('button_style_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('button_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ButtonStyle'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ButtonStyleMeta'])

        # Adding model 'CampaignButtonStyle'
        db.create_table('campaign_button_styles', (
            ('campaign_button_style_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('button_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ButtonStyle'])),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=9)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignButtonStyle'])

        # Adding model 'ChoiceSet'
        db.create_table('choice_sets', (
            ('choice_set_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSet'])

        # Adding model 'ChoiceSetAlgorithm'
        db.create_table('choice_set_algoritms', (
            ('choice_set_algorithm_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSetAlgorithm'])

        # Adding model 'CampaignChoiceSetAlgorithm'
        db.create_table('campaign_choice_set_algoritm', (
            ('campaign_choice_set_algoritm_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('choice_set_algorithm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSetAlgorithm'], db_column='choice_set_algoritm_id')),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=9)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignChoiceSetAlgorithm'])

        # Adding model 'CampaignChoiceSet'
        db.create_table('campaign_choice_sets', (
            ('campaign_choice_set_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('choice_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSet'])),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=9)),
            ('allow_generic', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('generic_url_slug', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignChoiceSet'])

        # Adding model 'CampaignFacesStyle'
        db.create_table('campaign_faces_styles', (
            ('campaign_faces_style_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('faces_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FacesStyle'])),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=9)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignFacesStyle'])

        # Adding model 'CampaignFBObjects'
        db.create_table('campaign_fb_objects', (
            ('campaign_fb_object_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'])),
            ('fb_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FBObject'])),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=9)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignFBObjects'])

        # Adding model 'CampaignGenericFBObjects'
        db.create_table('campaign_generic_fb_objects', (
            ('campaign_generic_fb_object_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('fb_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FBObject'])),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=9)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignGenericFBObjects'])

        # Adding model 'CampaignGlobalFilter'
        db.create_table('campaign_global_filters', (
            ('campaign_global_filter_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'])),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=9)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignGlobalFilter'])

        # Adding model 'CampaignMeta'
        db.create_table('campaign_meta', (
            ('campaign_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignMeta'])

        # Adding model 'CampaignMixModel'
        db.create_table('campaign_mix_models', (
            ('campaign_mix_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('mix_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.MixModel'])),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=9)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignMixModel'])

        # Adding model 'CampaignPropensityModel'
        db.create_table('campaign_propensity_models', (
            ('campaign_propensity_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('propensity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.PropensityModel'])),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=9)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignPropensityModel'])

        # Adding model 'CampaignProperties'
        db.create_table('campaign_properties', (
            ('campaign_property_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('client_faces_url', self.gf('django.db.models.fields.CharField')(max_length=2096)),
            ('client_thanks_url', self.gf('django.db.models.fields.CharField')(max_length=2096)),
            ('client_error_url', self.gf('django.db.models.fields.CharField')(max_length=2096)),
            ('fallback_campaign', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fallback_campaign', to=orm['targetshare.Campaign'], null=True)),
            ('fallback_content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ClientContent'], null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignProperties'])

        # Adding model 'CampaignProximityModel'
        db.create_table('campaign_proximity_models', (
            ('campaign_proximity_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('proximity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ProximityModel'])),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=9)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignProximityModel'])

        # Adding model 'ChoiceSetAlgorithmDefinition'
        db.create_table('choice_set_algoritm_definitions', (
            ('choice_set_algorithm_definition_id', self.gf('django.db.models.fields.AutoField')(primary_key=True, db_column='choice_set_algoritm_definition_id')),
            ('choice_set_algorithm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSetAlgorithm'], db_column='choice_set_algoritm_id')),
            ('algorithm_definition', self.gf('django.db.models.fields.TextField')(null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSetAlgorithmDefinition'])

        # Adding model 'ChoiceSetAlgorithmMeta'
        db.create_table('choice_set_algoritm_meta', (
            ('choice_set_algorithm_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True, db_column='choice_set_algoritm_meta_id')),
            ('choice_set_algorithm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSetAlgorithm'], db_column='choice_set_algoritm_id')),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSetAlgorithmMeta'])

        # Adding model 'ChoiceSetFilter'
        db.create_table('choice_set_filters', (
            ('choice_set_filter_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('choice_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSet'])),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'])),
            ('url_slug', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('propensity_model_type', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSetFilter'])

        # Adding model 'ChoiceSetMeta'
        db.create_table('choice_set_meta', (
            ('choice_set_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('choice_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSet'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSetMeta'])

        # Adding model 'ClientContent'
        db.create_table('client_content', (
            ('content_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=2048, null=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ClientContent'])

        # Adding model 'ClientDefault'
        db.create_table('client_defaults', (
            ('client_default_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'])),
            ('button_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ButtonStyle'], null=True)),
            ('faces_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FacesStyle'], null=True)),
            ('propensity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.PropensityModel'], null=True)),
            ('proximity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ProximityModel'], null=True)),
            ('mix_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.MixModel'], null=True)),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'], null=True)),
            ('choice_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSet'], null=True)),
            ('choice_set_algorithm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSetAlgorithm'], null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ClientDefault'])

        # Adding model 'Edge'
        db.create_table('edges', (
            ('fbid_source', self.gf('django.db.models.fields.BigIntegerField')()),
            ('fbid_target', self.gf('django.db.models.fields.BigIntegerField')()),
            ('post_likes', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('post_comms', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('stat_likes', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('stat_comms', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('wall_posts', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('wall_comms', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('tags', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('photos_target', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('photos_other', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('mut_friends', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['Edge'])

        # Adding unique constraint on 'Edge', fields ['fbid_source', 'fbid_target']
        db.create_unique('edges', ['fbid_source', 'fbid_target'])

        # Adding model 'Event'
        db.create_table('events', (
            ('session_id', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('fbid', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('friend_fbid', self.gf('django.db.models.fields.BigIntegerField')()),
            ('event_type', self.gf('django.db.models.fields.CharField')(max_length=64, db_column='type')),
            ('app_id', self.gf('django.db.models.fields.BigIntegerField')(db_column='appid')),
            ('content', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('activity_id', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['Event'])

        # Adding unique constraint on 'Event', fields ['session_id', 'campaign', 'content', 'fbid', 'friend_fbid', 'activity_id']
        db.create_unique('events', ['session_id', 'campaign_id', 'content', 'fbid', 'friend_fbid', 'activity_id'])

        # Adding model 'FaceExclusion'
        db.create_table('face_exclusions', (
            ('fbid', self.gf('django.db.models.fields.BigIntegerField')()),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ClientContent'])),
            ('friend_fbid', self.gf('django.db.models.fields.BigIntegerField')()),
            ('reason', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['FaceExclusion'])

        # Adding unique constraint on 'FaceExclusion', fields ['fbid', 'campaign', 'content', 'friend_fbid']
        db.create_unique('face_exclusions', ['fbid', 'campaign_id', 'content_id', 'friend_fbid'])

        # Adding model 'FacesStyle'
        db.create_table('faces_styles', (
            ('faces_style_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['FacesStyle'])

        # Adding model 'FacesStyleFiles'
        db.create_table('faces_style_files', (
            ('faces_style_file_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('faces_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FacesStyle'])),
            ('html_template', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('css_file', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['FacesStyleFiles'])

        # Adding model 'FacesStyleMeta'
        db.create_table('faces_style_meta', (
            ('faces_style_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('faces_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FacesStyle'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['FacesStyleMeta'])

        # Adding model 'FBObjectAttribute'
        db.create_table('fb_object_attributes', (
            ('fb_object_attributes_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fb_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FBObject'])),
            ('og_action', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('og_type', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('og_title', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('og_image', self.gf('django.db.models.fields.CharField')(max_length=2096, null=True)),
            ('og_description', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('page_title', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('sharing_prompt', self.gf('django.db.models.fields.CharField')(max_length=2096, null=True)),
            ('msg1_pre', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('msg1_post', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('msg2_pre', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('msg2_post', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('url_slug', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['FBObjectAttribute'])

        # Adding model 'FBObjectMeta'
        db.create_table('fb_object_meta', (
            ('fb_object_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fb_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FBObject'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['FBObjectMeta'])

        # Adding model 'FBObject'
        db.create_table('fb_objects', (
            ('fb_object_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['FBObject'])

        # Adding model 'FilterFeature'
        db.create_table('filter_features', (
            ('filter_feature_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'])),
            ('feature', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('operator', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('value_type', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['FilterFeature'])

        # Adding model 'FilterMeta'
        db.create_table('filter_meta', (
            ('filter_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['FilterMeta'])

        # Adding model 'Filter'
        db.create_table('filters', (
            ('filter_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['Filter'])

        # Adding model 'MixModelDefinition'
        db.create_table('mix_model_definitions', (
            ('mix_model_definition_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mix_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.MixModel'])),
            ('model_definition', self.gf('django.db.models.fields.TextField')(null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['MixModelDefinition'])

        # Adding model 'MixModelMeta'
        db.create_table('mix_model_meta', (
            ('mix_model_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mix_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.MixModel'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['MixModelMeta'])

        # Adding model 'MixModel'
        db.create_table('mix_models', (
            ('mix_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['MixModel'])

        # Adding model 'PropensityModelDefinition'
        db.create_table('propensity_model_definitions', (
            ('propensity_model_definition_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('propensity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.PropensityModel'])),
            ('propensity_model_type', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('model_definition', self.gf('django.db.models.fields.TextField')(null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['PropensityModelDefinition'])

        # Adding model 'PropensityModelMeta'
        db.create_table('propensity_model_meta', (
            ('propensity_model_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('propensity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.PropensityModel'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['PropensityModelMeta'])

        # Adding model 'PropensityModel'
        db.create_table('propensity_models', (
            ('propensity_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['PropensityModel'])

        # Adding model 'ProximityModelDefinition'
        db.create_table('proximity_model_definitions', (
            ('proximity_model_definition_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('proximity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ProximityModel'])),
            ('proximity_model_type', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
            ('model_definition', self.gf('django.db.models.fields.TextField')(null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ProximityModelDefinition'])

        # Adding model 'ProximityModelMeta'
        db.create_table('proximity_model_meta', (
            ('proximity_model_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('proximity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ProximityModel'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ProximityModelMeta'])

        # Adding model 'ProximityModel'
        db.create_table('proximity_models', (
            ('proximity_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'targetshare', ['ProximityModel'])

        # Adding model 'ShareMessage'
        db.create_table('share_messages', (
            ('activity_id', self.gf('django.db.models.fields.BigIntegerField')(default=0, primary_key=True)),
            ('fbid', self.gf('django.db.models.fields.BigIntegerField')()),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ClientContent'])),
            ('message', self.gf('django.db.models.fields.TextField')(null=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ShareMessage'])

        # Adding model 'Token'
        db.create_table('tokens', (
            ('fbid', self.gf('django.db.models.fields.BigIntegerField')(primary_key=True)),
            ('app_id', self.gf('django.db.models.fields.BigIntegerField')(db_column='appid')),
            ('owner_id', self.gf('django.db.models.fields.BigIntegerField')(db_column='ownerid')),
            ('token', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('expires', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['Token'])

        # Adding unique constraint on 'Token', fields ['fbid', 'app_id', 'owner_id']
        db.create_unique('tokens', ['fbid', 'appid', 'ownerid'])

        # Adding model 'UserClient'
        db.create_table('user_clients', (
            ('fbid', self.gf('django.db.models.fields.BigIntegerField')()),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'])),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['UserClient'])

        # Adding unique constraint on 'UserClient', fields ['fbid', 'client']
        db.create_unique('user_clients', ['fbid', 'client_id'])

        # Adding model 'User'
        db.create_table('users', (
            ('fbid', self.gf('django.db.models.fields.BigIntegerField')(primary_key=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, db_column='fname')),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, db_column='lname')),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=8, null=True)),
            ('birthday', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['User'])


    def backwards(self, orm):
        # Removing unique constraint on 'UserClient', fields ['fbid', 'client']
        db.delete_unique('user_clients', ['fbid', 'client_id'])

        # Removing unique constraint on 'Token', fields ['fbid', 'app_id', 'owner_id']
        db.delete_unique('tokens', ['fbid', 'appid', 'ownerid'])

        # Removing unique constraint on 'FaceExclusion', fields ['fbid', 'campaign', 'content', 'friend_fbid']
        db.delete_unique('face_exclusions', ['fbid', 'campaign_id', 'content_id', 'friend_fbid'])

        # Removing unique constraint on 'Event', fields ['session_id', 'campaign', 'content', 'fbid', 'friend_fbid', 'activity_id']
        db.delete_unique('events', ['session_id', 'campaign_id', 'content', 'fbid', 'friend_fbid', 'activity_id'])

        # Removing unique constraint on 'Edge', fields ['fbid_source', 'fbid_target']
        db.delete_unique('edges', ['fbid_source', 'fbid_target'])

        # Deleting model 'Assignment'
        db.delete_table('assignments')

        # Deleting model 'Client'
        db.delete_table('clients')

        # Deleting model 'Campaign'
        db.delete_table('campaigns')

        # Deleting model 'ButtonStyle'
        db.delete_table('button_styles')

        # Deleting model 'ButtonStyleFile'
        db.delete_table('button_style_files')

        # Deleting model 'ButtonStyleMeta'
        db.delete_table('button_style_meta')

        # Deleting model 'CampaignButtonStyle'
        db.delete_table('campaign_button_styles')

        # Deleting model 'ChoiceSet'
        db.delete_table('choice_sets')

        # Deleting model 'ChoiceSetAlgorithm'
        db.delete_table('choice_set_algoritms')

        # Deleting model 'CampaignChoiceSetAlgorithm'
        db.delete_table('campaign_choice_set_algoritm')

        # Deleting model 'CampaignChoiceSet'
        db.delete_table('campaign_choice_set')

        # Deleting model 'CampaignFacesStyle'
        db.delete_table('campaign_faces_styles')

        # Deleting model 'CampaignFBObjects'
        db.delete_table('campaign_fb_objects')

        # Deleting model 'CampaignGenericFBObjects'
        db.delete_table('campaign_generic_fb_objects')

        # Deleting model 'CampaignGlobalFilter'
        db.delete_table('campaign_global_filter')

        # Deleting model 'CampaignMeta'
        db.delete_table('campaign_meta')

        # Deleting model 'CampaignMixModel'
        db.delete_table('campaign_mix_models')

        # Deleting model 'CampaignPropensityModel'
        db.delete_table('campaign_propensity_models')

        # Deleting model 'CampaignProperties'
        db.delete_table('campaign_properties')

        # Deleting model 'CampaignProximityModel'
        db.delete_table('campaign_proximity_models')

        # Deleting model 'ChoiceSetAlgorithmDefinition'
        db.delete_table('choice_set_algoritm_definitions')

        # Deleting model 'ChoiceSetAlgorithmMeta'
        db.delete_table('choice_set_algoritm_meta')

        # Deleting model 'ChoiceSetFilter'
        db.delete_table('choice_set_filters')

        # Deleting model 'ChoiceSetMeta'
        db.delete_table('choice_set_meta')

        # Deleting model 'ClientContent'
        db.delete_table('client_content')

        # Deleting model 'ClientDefault'
        db.delete_table('client_defaults')

        # Deleting model 'Edge'
        db.delete_table('edges')

        # Deleting model 'Event'
        db.delete_table('events')

        # Deleting model 'FaceExclusion'
        db.delete_table('face_exclusions')

        # Deleting model 'FacesStyle'
        db.delete_table('faces_styles')

        # Deleting model 'FacesStyleFiles'
        db.delete_table('faces_style_files')

        # Deleting model 'FacesStyleMeta'
        db.delete_table('faces_style_meta')

        # Deleting model 'FBObjectAttribute'
        db.delete_table('fb_object_attributes')

        # Deleting model 'FBObjectMeta'
        db.delete_table('fb_object_meta')

        # Deleting model 'FBObject'
        db.delete_table('fb_objects')

        # Deleting model 'FilterFeature'
        db.delete_table('filter_features')

        # Deleting model 'FilterMeta'
        db.delete_table('filter_meta')

        # Deleting model 'Filter'
        db.delete_table('filters')

        # Deleting model 'MixModelDefinition'
        db.delete_table('mix_model_definitions')

        # Deleting model 'MixModelMeta'
        db.delete_table('mix_model_meta')

        # Deleting model 'MixModel'
        db.delete_table('mix_models')

        # Deleting model 'PropensityModelDefinition'
        db.delete_table('propensity_model_definitions')

        # Deleting model 'PropensityModelMeta'
        db.delete_table('propensity_model_meta')

        # Deleting model 'PropensityModel'
        db.delete_table('propensity_models')

        # Deleting model 'ProximityModelDefinition'
        db.delete_table('proximity_model_definitions')

        # Deleting model 'ProximityModelMeta'
        db.delete_table('proximity_model_meta')

        # Deleting model 'ProximityModel'
        db.delete_table('proximity_models')

        # Deleting model 'ShareMessage'
        db.delete_table('share_messages')

        # Deleting model 'Token'
        db.delete_table('tokens')

        # Deleting model 'UserClient'
        db.delete_table('user_clients')

        # Deleting model 'User'
        db.delete_table('users')


    models = {
        u'targetshare.assignment': {
            'Meta': {'object_name': 'Assignment', 'db_table': "'assignments'"},
            'assign_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'chosen_from_rows': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'chosen_from_table': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ClientContent']"}),
            'feature_row': ('django.db.models.fields.IntegerField', [], {}),
            'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'random_assign': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'targetshare.buttonstyle': {
            'Meta': {'object_name': 'ButtonStyle', 'db_table': "'button_styles'"},
            'button_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'targetshare.buttonstylefile': {
            'Meta': {'object_name': 'ButtonStyleFile', 'db_table': "'button_style_files'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ButtonStyle']"}),
            'button_style_file_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'css_file': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'html_template': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.buttonstylemeta': {
            'Meta': {'object_name': 'ButtonStyleMeta', 'db_table': "'button_style_meta'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ButtonStyle']"}),
            'button_style_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'targetshare.campaign': {
            'Meta': {'object_name': 'Campaign', 'db_table': "'campaigns'"},
            'campaign_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'targetshare.campaignbuttonstyle': {
            'Meta': {'object_name': 'CampaignButtonStyle', 'db_table': "'campaign_button_styles'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ButtonStyle']"}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_button_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '9'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.campaignchoiceset': {
            'Meta': {'object_name': 'CampaignChoiceSet', 'db_table': "'campaign_choice_set'"},
            'allow_generic': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_choice_set_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSet']"}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'generic_url_slug': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '9'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.campaignchoicesetalgorithm': {
            'Meta': {'object_name': 'CampaignChoiceSetAlgorithm', 'db_table': "'campaign_choice_set_algoritm'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_choice_set_algoritm_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSetAlgorithm']", 'db_column': "'choice_set_algoritm_id'"}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '9'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.campaignfacesstyle': {
            'Meta': {'object_name': 'CampaignFacesStyle', 'db_table': "'campaign_faces_styles'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_faces_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FacesStyle']"}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '9'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.campaignfbobjects': {
            'Meta': {'object_name': 'CampaignFBObjects', 'db_table': "'campaign_fb_objects'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_fb_object_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FBObject']"}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']"}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '9'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.campaigngenericfbobjects': {
            'Meta': {'object_name': 'CampaignGenericFBObjects', 'db_table': "'campaign_generic_fb_objects'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_generic_fb_object_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FBObject']"}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '9'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.campaignglobalfilter': {
            'Meta': {'object_name': 'CampaignGlobalFilter', 'db_table': "'campaign_global_filter'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_global_filter_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']"}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '9'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.campaignmeta': {
            'Meta': {'object_name': 'CampaignMeta', 'db_table': "'campaign_meta'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'targetshare.campaignmixmodel': {
            'Meta': {'object_name': 'CampaignMixModel', 'db_table': "'campaign_mix_models'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_mix_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.MixModel']"}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '9'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.campaignpropensitymodel': {
            'Meta': {'object_name': 'CampaignPropensityModel', 'db_table': "'campaign_propensity_models'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_propensity_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.PropensityModel']"}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '9'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.campaignproperties': {
            'Meta': {'object_name': 'CampaignProperties', 'db_table': "'campaign_properties'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_property_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'client_error_url': ('django.db.models.fields.CharField', [], {'max_length': '2096'}),
            'client_faces_url': ('django.db.models.fields.CharField', [], {'max_length': '2096'}),
            'client_thanks_url': ('django.db.models.fields.CharField', [], {'max_length': '2096'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'fallback_campaign': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fallback_campaign'", 'to': u"orm['targetshare.Campaign']"}),
            'fallback_content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ClientContent']"}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.campaignproximitymodel': {
            'Meta': {'object_name': 'CampaignProximityModel', 'db_table': "'campaign_proximity_models'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'campaign_proximity_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ProximityModel']"}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '9'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.choiceset': {
            'Meta': {'object_name': 'ChoiceSet', 'db_table': "'choice_sets'"},
            'choice_set_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'targetshare.choicesetalgorithm': {
            'Meta': {'object_name': 'ChoiceSetAlgorithm', 'db_table': "'choice_set_algoritms'"},
            'choice_set_algorithm_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'})
        },
        u'targetshare.choicesetalgorithmdefinition': {
            'Meta': {'object_name': 'ChoiceSetAlgorithmDefinition', 'db_table': "'choice_set_algoritm_definitions'"},
            'algorithm_definition': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSetAlgorithm']", 'db_column': "'choice_set_algoritm_id'"}),
            'choice_set_algorithm_definition_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'db_column': "'choice_set_algoritm_definition_id'"}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.choicesetalgorithmmeta': {
            'Meta': {'object_name': 'ChoiceSetAlgorithmMeta', 'db_table': "'choice_set_algoritm_meta'"},
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSetAlgorithm']", 'db_column': "'choice_set_algoritm_id'"}),
            'choice_set_algorithm_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'db_column': "'choice_set_algoritm_meta_id'"}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        u'targetshare.choicesetfilter': {
            'Meta': {'object_name': 'ChoiceSetFilter', 'db_table': "'choice_set_filters'"},
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSet']"}),
            'choice_set_filter_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']"}),
            'propensity_model_type': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'url_slug': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'targetshare.choicesetmeta': {
            'Meta': {'object_name': 'ChoiceSetMeta', 'db_table': "'choice_set_meta'"},
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSet']"}),
            'choice_set_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        u'targetshare.client': {
            'Meta': {'object_name': 'Client', 'db_table': "'clients'"},
            'client_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'fb_app_id': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'fb_app_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'subdomain': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'targetshare.clientcontent': {
            'Meta': {'object_name': 'ClientContent', 'db_table': "'client_content'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']"}),
            'content_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True'})
        },
        u'targetshare.clientdefault': {
            'Meta': {'object_name': 'ClientDefault', 'db_table': "'client_defaults'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ButtonStyle']", 'null': 'True'}),
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSet']", 'null': 'True'}),
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSetAlgorithm']", 'null': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']"}),
            'client_default_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FacesStyle']", 'null': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']", 'null': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.MixModel']", 'null': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.PropensityModel']", 'null': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ProximityModel']", 'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.edge': {
            'Meta': {'unique_together': "(('fbid_source', 'fbid_target'),)", 'object_name': 'Edge', 'db_table': "'edges'"},
            'fbid_source': ('django.db.models.fields.BigIntegerField', [], {}),
            'fbid_target': ('django.db.models.fields.BigIntegerField', [], {}),
            'mut_friends': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'photos_other': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'photos_target': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'post_comms': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'post_likes': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'stat_comms': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'stat_likes': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'tags': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'wall_comms': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'wall_posts': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        u'targetshare.event': {
            'Meta': {'unique_together': "(('session_id', 'campaign', 'content', 'fbid', 'friend_fbid', 'activity_id'),)", 'object_name': 'Event', 'db_table': "'events'"},
            'activity_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'app_id': ('django.db.models.fields.BigIntegerField', [], {'db_column': "'appid'"}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'client_content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ClientContent']", 'null': 'True', 'db_column': "'client_id'"}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_column': "'type'"}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'friend_fbid': ('django.db.models.fields.BigIntegerField', [], {}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'targetshare.faceexclusion': {
            'Meta': {'unique_together': "(('fbid', 'campaign', 'content', 'friend_fbid'),)", 'object_name': 'FaceExclusion', 'db_table': "'face_exclusions'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ClientContent']"}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {}),
            'friend_fbid': ('django.db.models.fields.BigIntegerField', [], {}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'targetshare.facesstyle': {
            'Meta': {'object_name': 'FacesStyle', 'db_table': "'faces_styles'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'faces_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'targetshare.facesstylefiles': {
            'Meta': {'object_name': 'FacesStyleFiles', 'db_table': "'faces_style_files'"},
            'css_file': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FacesStyle']"}),
            'faces_style_file_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'html_template': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.facesstylemeta': {
            'Meta': {'object_name': 'FacesStyleMeta', 'db_table': "'faces_style_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FacesStyle']"}),
            'faces_style_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        u'targetshare.fbobject': {
            'Meta': {'object_name': 'FBObject', 'db_table': "'fb_objects'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'fb_object_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'})
        },
        u'targetshare.fbobjectattribute': {
            'Meta': {'object_name': 'FBObjectAttribute', 'db_table': "'fb_object_attributes'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FBObject']"}),
            'fb_object_attributes_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msg1_post': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'msg1_pre': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'msg2_post': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'msg2_pre': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'og_action': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'og_description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'og_image': ('django.db.models.fields.CharField', [], {'max_length': '2096', 'null': 'True'}),
            'og_title': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'og_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'sharing_prompt': ('django.db.models.fields.CharField', [], {'max_length': '2096', 'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'url_slug': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'})
        },
        u'targetshare.fbobjectmeta': {
            'Meta': {'object_name': 'FBObjectMeta', 'db_table': "'fb_object_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FBObject']"}),
            'fb_object_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        u'targetshare.filter': {
            'Meta': {'object_name': 'Filter', 'db_table': "'filters'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'filter_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'})
        },
        u'targetshare.filterfeature': {
            'Meta': {'object_name': 'FilterFeature', 'db_table': "'filter_features'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'feature': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']"}),
            'filter_feature_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'operator': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'value_type': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'targetshare.filtermeta': {
            'Meta': {'object_name': 'FilterMeta', 'db_table': "'filter_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']"}),
            'filter_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        u'targetshare.mixmodel': {
            'Meta': {'object_name': 'MixModel', 'db_table': "'mix_models'"},
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mix_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'})
        },
        u'targetshare.mixmodeldefinition': {
            'Meta': {'object_name': 'MixModelDefinition', 'db_table': "'mix_model_definitions'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.MixModel']"}),
            'mix_model_definition_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_definition': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.mixmodelmeta': {
            'Meta': {'object_name': 'MixModelMeta', 'db_table': "'mix_model_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.MixModel']"}),
            'mix_model_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        u'targetshare.propensitymodel': {
            'Meta': {'object_name': 'PropensityModel', 'db_table': "'propensity_models'"},
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'propensity_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'targetshare.propensitymodeldefinition': {
            'Meta': {'object_name': 'PropensityModelDefinition', 'db_table': "'propensity_model_definitions'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'model_definition': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.PropensityModel']"}),
            'propensity_model_definition_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'propensity_model_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.propensitymodelmeta': {
            'Meta': {'object_name': 'PropensityModelMeta', 'db_table': "'propensity_model_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.PropensityModel']"}),
            'propensity_model_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        u'targetshare.proximitymodel': {
            'Meta': {'object_name': 'ProximityModel', 'db_table': "'proximity_models'"},
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'proximity_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'targetshare.proximitymodeldefinition': {
            'Meta': {'object_name': 'ProximityModelDefinition', 'db_table': "'proximity_model_definitions'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'model_definition': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ProximityModel']"}),
            'proximity_model_definition_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'proximity_model_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'targetshare.proximitymodelmeta': {
            'Meta': {'object_name': 'ProximityModelMeta', 'db_table': "'proximity_model_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ProximityModel']"}),
            'proximity_model_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        u'targetshare.sharemessage': {
            'Meta': {'object_name': 'ShareMessage', 'db_table': "'share_messages'"},
            'activity_id': ('django.db.models.fields.BigIntegerField', [], {'default': '0', 'primary_key': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ClientContent']"}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'targetshare.token': {
            'Meta': {'unique_together': "(('fbid', 'app_id', 'owner_id'),)", 'object_name': 'Token', 'db_table': "'tokens'"},
            'app_id': ('django.db.models.fields.BigIntegerField', [], {'db_column': "'appid'"}),
            'expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'owner_id': ('django.db.models.fields.BigIntegerField', [], {'db_column': "'ownerid'"}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'targetshare.user': {
            'Meta': {'object_name': 'User', 'db_table': "'users'"},
            'birthday': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'db_column': "'fname'"}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'db_column': "'lname'"}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'targetshare.userclient': {
            'Meta': {'unique_together': "(('fbid', 'client'),)", 'object_name': 'UserClient', 'db_table': "'user_clients'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {}),
        }
    }

    complete_apps = ['targetshare']
