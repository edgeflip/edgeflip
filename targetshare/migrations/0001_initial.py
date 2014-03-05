# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Assignment'
        db.create_table(u'assignments', (
            ('session_id', self.gf('django.db.models.fields.CharField')(max_length=128L, blank=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ClientContent'], null=True, blank=True)),
            ('feature_type', self.gf('django.db.models.fields.CharField')(max_length=128L, blank=True)),
            ('feature_row', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('random_assign', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('assign_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('chosen_from_table', self.gf('django.db.models.fields.CharField')(max_length=128L, blank=True)),
            ('chosen_from_rows', self.gf('django.db.models.fields.CharField')(max_length=128L, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['Assignment'])

        # Adding model 'ButtonStyleFile'
        db.create_table(u'button_style_files', (
            ('button_style_file_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('button_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ButtonStyle'], null=True, blank=True)),
            ('html_template', self.gf('django.db.models.fields.CharField')(max_length=128L, blank=True)),
            ('css_file', self.gf('django.db.models.fields.CharField')(max_length=128L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ButtonStyleFile'])

        # Adding model 'ButtonStyleMeta'
        db.create_table(u'button_style_meta', (
            ('button_style_meta_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('button_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ButtonStyle'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ButtonStyleMeta'])

        # Adding model 'ButtonStyle'
        db.create_table(u'button_styles', (
            ('button_style_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ButtonStyle'])

        # Adding model 'CampaignButtonStyle'
        db.create_table(u'campaign_button_styles', (
            ('campaign_button_style_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('button_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ButtonStyle'], null=True, blank=True)),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=9, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignButtonStyle'])

        # Adding model 'CampaignChoiceSetAlgorithm'
        db.create_table(u'campaign_choice_set_algoritm', (
            ('campaign_choice_set_algorithm_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True, db_column=u'campaign_choice_set_algoritm_id')),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('choice_set_algorithm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSetAlgorithm'], null=True, db_column=u'choice_set_algoritm_id', blank=True)),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=9, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignChoiceSetAlgorithm'])

        # Adding model 'CampaignChoiceSet'
        db.create_table(u'campaign_choice_sets', (
            ('campaign_choice_set_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('choice_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSet'], null=True, blank=True)),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=9, blank=True)),
            ('allow_generic', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('generic_url_slug', self.gf('django.db.models.fields.CharField')(max_length=64L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignChoiceSet'])

        # Adding model 'CampaignFacesStyle'
        db.create_table(u'campaign_faces_styles', (
            ('campaign_faces_style_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('faces_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FacesStyle'], null=True, blank=True)),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=9, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignFacesStyle'])

        # Adding model 'CampaignFBObjects'
        db.create_table(u'campaign_fb_objects', (
            ('campaign_fb_object_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'], null=True, blank=True)),
            ('fb_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FBObject'], null=True, blank=True)),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=9, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignFBObjects'])

        # Adding model 'CampaignGenericFbObjects'
        db.create_table(u'campaign_generic_fb_objects', (
            ('campaign_generic_fb_object_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('fb_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FBObject'], null=True, blank=True)),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=9, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignGenericFbObjects'])

        # Adding model 'CampaignGlobalFilter'
        db.create_table(u'campaign_global_filters', (
            ('campaign_global_filter_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'], null=True, blank=True)),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=9, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignGlobalFilter'])

        # Adding model 'CampaignMeta'
        db.create_table(u'campaign_meta', (
            ('campaign_meta_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignMeta'])

        # Adding model 'CampaignMixModel'
        db.create_table(u'campaign_mix_models', (
            ('campaign_mix_model_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('mix_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.MixModel'], null=True, blank=True)),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=9, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignMixModel'])

        # Adding model 'CampaignPropensityModel'
        db.create_table(u'campaign_propensity_models', (
            ('campaign_propensity_model_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('propensity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.PropensityModel'], null=True, blank=True)),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=9, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignPropensityModel'])

        # Adding model 'CampaignProperties'
        db.create_table(u'campaign_properties', (
            ('campaign_property_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('client_faces_url', self.gf('django.db.models.fields.CharField')(max_length=2096L, blank=True)),
            ('client_thanks_url', self.gf('django.db.models.fields.CharField')(max_length=2096L, blank=True)),
            ('client_error_url', self.gf('django.db.models.fields.CharField')(max_length=2096L, blank=True)),
            ('fallback_campaign', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'fallback', null=True, to=orm['targetshare.Campaign'])),
            ('fallback_content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ClientContent'], null=True, blank=True)),
            ('fallback_is_cascading', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('min_friends', self.gf('django.db.models.fields.IntegerField')()),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignProperties'])

        # Adding model 'CampaignProximityModel'
        db.create_table(u'campaign_proximity_models', (
            ('campaign_proximity_model_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('proximity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ProximityModel'], null=True, blank=True)),
            ('rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=9, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['CampaignProximityModel'])

        # Adding model 'Campaign'
        db.create_table(u'campaigns', (
            ('campaign_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['Campaign'])

        # Adding model 'ChoiceSetAlgorithmDefinition'
        db.create_table(u'choice_set_algoritm_definitions', (
            ('choice_set_algorithm_definition_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True, db_column=u'choice_set_algoritm_definition_id')),
            ('choice_set_algorithm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSetAlgorithm'], null=True, db_column=u'choice_set_algoritm_id', blank=True)),
            ('algorithm_definition', self.gf('django.db.models.fields.CharField')(max_length=4096L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSetAlgorithmDefinition'])

        # Adding model 'ChoiceSetAlgorithmMeta'
        db.create_table(u'choice_set_algoritm_meta', (
            ('choice_set_algorithm_meta_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True, db_column=u'choice_set_algoritm_meta_id')),
            ('choice_set_algorithm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSetAlgorithm'], null=True, db_column=u'choice_set_algoritm_id', blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSetAlgorithmMeta'])

        # Adding model 'ChoiceSetAlgorithm'
        db.create_table(u'choice_set_algoritms', (
            ('choice_set_algorithm_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSetAlgorithm'])

        # Adding model 'ChoiceSetFilter'
        db.create_table(u'choice_set_filters', (
            ('choice_set_filter_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('choice_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSet'], null=True, blank=True)),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'], null=True, blank=True)),
            ('url_slug', self.gf('django.db.models.fields.CharField')(max_length=64L, blank=True)),
            ('propensity_model_type', self.gf('django.db.models.fields.CharField')(max_length=32L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSetFilter'])

        # Adding model 'ChoiceSetMeta'
        db.create_table(u'choice_set_meta', (
            ('choice_set_meta_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('choice_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSet'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSetMeta'])

        # Adding model 'ChoiceSet'
        db.create_table(u'choice_sets', (
            ('choice_set_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ChoiceSet'])

        # Adding model 'ClientContent'
        db.create_table(u'client_content', (
            ('content_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=2048L, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ClientContent'])

        # Adding model 'ClientDefault'
        db.create_table(u'client_defaults', (
            ('client_default_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'], null=True, blank=True)),
            ('button_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ButtonStyle'], null=True, blank=True)),
            ('faces_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FacesStyle'], null=True, blank=True)),
            ('propensity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.PropensityModel'], null=True, blank=True)),
            ('proximity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ProximityModel'], null=True, blank=True)),
            ('mix_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.MixModel'], null=True, blank=True)),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'], null=True, blank=True)),
            ('choice_set', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSet'], null=True, blank=True)),
            ('choice_set_algorithm', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSetAlgorithm'], null=True, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ClientDefault'])

        # Adding model 'Client'
        db.create_table(u'clients', (
            ('client_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, blank=True)),
            ('fb_app_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('fb_app_id', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('subdomain', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'targetshare', ['Client'])

        # Adding model 'Event'
        db.create_table(u'events', (
            ('session_id', self.gf('django.db.models.fields.CharField')(max_length=128L, blank=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('client_content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ClientContent'], null=True, db_column=u'content_id', blank=True)),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=32L, blank=True)),
            ('fbid', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('friend_fbid', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('event_type', self.gf('django.db.models.fields.CharField')(max_length=64L, blank=True, db_column=u'type')),
            ('app_id', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True, db_column=u'appid')),
            ('content', self.gf('django.db.models.fields.CharField')(max_length=128L, blank=True)),
            ('activity_id', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'targetshare', ['Event'])

        # Adding model 'FaceExclusion'
        db.create_table(u'face_exclusions', (
            ('fbid', self.gf('django.db.models.fields.BigIntegerField')()),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'])),
            ('content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ClientContent'])),
            ('friend_fbid', self.gf('django.db.models.fields.BigIntegerField')()),
            ('reason', self.gf('django.db.models.fields.CharField')(max_length=512L, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'targetshare', ['FaceExclusion'])

        # Adding model 'FacesStyleFiles'
        db.create_table(u'faces_style_files', (
            ('faces_style_file_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('faces_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FacesStyle'], null=True, blank=True)),
            ('html_template', self.gf('django.db.models.fields.CharField')(max_length=128L, blank=True)),
            ('css_file', self.gf('django.db.models.fields.CharField')(max_length=128L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['FacesStyleFiles'])

        # Adding model 'FacesStyleMeta'
        db.create_table(u'faces_style_meta', (
            ('faces_style_meta_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('faces_style', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FacesStyle'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['FacesStyleMeta'])

        # Adding model 'FacesStyle'
        db.create_table(u'faces_styles', (
            ('faces_style_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['FacesStyle'])

        # Adding model 'FBObjectAttribute'
        db.create_table(u'fb_object_attributes', (
            ('fb_object_attributes_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('fb_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FBObject'], null=True, blank=True)),
            ('og_action', self.gf('django.db.models.fields.CharField')(max_length=64L, blank=True)),
            ('og_type', self.gf('django.db.models.fields.CharField')(max_length=64L, blank=True)),
            ('og_title', self.gf('django.db.models.fields.CharField')(max_length=128L, blank=True)),
            ('og_image', self.gf('django.db.models.fields.CharField')(max_length=2096L, blank=True)),
            ('og_description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('page_title', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('sharing_prompt', self.gf('django.db.models.fields.CharField')(max_length=2096L, blank=True)),
            ('msg1_pre', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('msg1_post', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('msg2_pre', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('msg2_post', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('url_slug', self.gf('django.db.models.fields.CharField')(max_length=64L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['FBObjectAttribute'])

        # Adding model 'FBObjectMeta'
        db.create_table(u'fb_object_meta', (
            ('fb_object_meta_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('fb_object', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.FBObject'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['FBObjectMeta'])

        # Adding model 'FBObject'
        db.create_table(u'fb_objects', (
            ('fb_object_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['FBObject'])

        # Adding model 'FilterFeature'
        db.create_table(u'filter_features', (
            ('filter_feature_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'], null=True, blank=True)),
            ('feature', self.gf('django.db.models.fields.CharField')(max_length=64L, blank=True)),
            ('operator', self.gf('django.db.models.fields.CharField')(max_length=32L, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('value_type', self.gf('django.db.models.fields.CharField')(max_length=32L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['FilterFeature'])

        # Adding model 'FilterMeta'
        db.create_table(u'filter_meta', (
            ('filter_meta_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('filter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Filter'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['FilterMeta'])

        # Adding model 'Filter'
        db.create_table(u'filters', (
            ('filter_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['Filter'])

        # Adding model 'MixModelDefinition'
        db.create_table(u'mix_model_definitions', (
            ('mix_model_definition_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('mix_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.MixModel'], null=True, blank=True)),
            ('model_definition', self.gf('django.db.models.fields.CharField')(max_length=4096L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['MixModelDefinition'])

        # Adding model 'MixModelMeta'
        db.create_table(u'mix_model_meta', (
            ('mix_model_meta_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('mix_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.MixModel'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['MixModelMeta'])

        # Adding model 'MixModel'
        db.create_table(u'mix_models', (
            ('mix_model_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['MixModel'])

        # Adding model 'PropensityModelDefinition'
        db.create_table(u'propensity_model_definitions', (
            ('propensity_model_definition_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('propensity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.PropensityModel'], null=True, blank=True)),
            ('propensity_model_type', self.gf('django.db.models.fields.CharField')(max_length=64L, blank=True)),
            ('model_definition', self.gf('django.db.models.fields.CharField')(max_length=4096L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['PropensityModelDefinition'])

        # Adding model 'PropensityModelMeta'
        db.create_table(u'propensity_model_meta', (
            ('propensity_model_meta_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('propensity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.PropensityModel'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['PropensityModelMeta'])

        # Adding model 'PropensityModel'
        db.create_table(u'propensity_models', (
            ('proximity_model_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['PropensityModel'])

        # Adding model 'ProximityModelDefinition'
        db.create_table(u'proximity_model_definitions', (
            ('proximity_model_definition_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('proximity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ProximityModel'], null=True, blank=True)),
            ('model_definition', self.gf('django.db.models.fields.CharField')(max_length=4096L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ProximityModelDefinition'])

        # Adding model 'ProximityModelMeta'
        db.create_table(u'proximity_model_meta', (
            ('proximity_model_meta_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('proximity_model', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ProximityModel'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('start_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('end_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ProximityModelMeta'])

        # Adding model 'ProximityModel'
        db.create_table(u'proximity_models', (
            ('proximity_model_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024L, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
            ('delete_dt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'targetshare', ['ProximityModel'])

        # Adding model 'ShareMessage'
        db.create_table(u'share_messages', (
            ('activity_id', self.gf('django.db.models.fields.BigIntegerField')(primary_key=True)),
            ('fbid', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True, blank=True)),
            ('content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ClientContent'], null=True, blank=True)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=4096L, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'targetshare', ['ShareMessage'])

        # Adding model 'UserClient'
        db.create_table(u'user_clients', (
            ('fbid', self.gf('django.db.models.fields.BigIntegerField')()),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Client'])),
            ('create_dt', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'targetshare', ['UserClient'])


    def backwards(self, orm):
        # Deleting model 'Assignment'
        db.delete_table(u'assignments')

        # Deleting model 'ButtonStyleFile'
        db.delete_table(u'button_style_files')

        # Deleting model 'ButtonStyleMeta'
        db.delete_table(u'button_style_meta')

        # Deleting model 'ButtonStyle'
        db.delete_table(u'button_styles')

        # Deleting model 'CampaignButtonStyle'
        db.delete_table(u'campaign_button_styles')

        # Deleting model 'CampaignChoiceSetAlgorithm'
        db.delete_table(u'campaign_choice_set_algoritm')

        # Deleting model 'CampaignChoiceSet'
        db.delete_table(u'campaign_choice_sets')

        # Deleting model 'CampaignFacesStyle'
        db.delete_table(u'campaign_faces_styles')

        # Deleting model 'CampaignFBObjects'
        db.delete_table(u'campaign_fb_objects')

        # Deleting model 'CampaignGenericFbObjects'
        db.delete_table(u'campaign_generic_fb_objects')

        # Deleting model 'CampaignGlobalFilter'
        db.delete_table(u'campaign_global_filters')

        # Deleting model 'CampaignMeta'
        db.delete_table(u'campaign_meta')

        # Deleting model 'CampaignMixModel'
        db.delete_table(u'campaign_mix_models')

        # Deleting model 'CampaignPropensityModel'
        db.delete_table(u'campaign_propensity_models')

        # Deleting model 'CampaignProperties'
        db.delete_table(u'campaign_properties')

        # Deleting model 'CampaignProximityModel'
        db.delete_table(u'campaign_proximity_models')

        # Deleting model 'Campaign'
        db.delete_table(u'campaigns')

        # Deleting model 'ChoiceSetAlgorithmDefinition'
        db.delete_table(u'choice_set_algoritm_definitions')

        # Deleting model 'ChoiceSetAlgorithmMeta'
        db.delete_table(u'choice_set_algoritm_meta')

        # Deleting model 'ChoiceSetAlgorithm'
        db.delete_table(u'choice_set_algoritms')

        # Deleting model 'ChoiceSetFilter'
        db.delete_table(u'choice_set_filters')

        # Deleting model 'ChoiceSetMeta'
        db.delete_table(u'choice_set_meta')

        # Deleting model 'ChoiceSet'
        db.delete_table(u'choice_sets')

        # Deleting model 'ClientContent'
        db.delete_table(u'client_content')

        # Deleting model 'ClientDefault'
        db.delete_table(u'client_defaults')

        # Deleting model 'Client'
        db.delete_table(u'clients')

        # Deleting model 'Event'
        db.delete_table(u'events')

        # Deleting model 'FaceExclusion'
        db.delete_table(u'face_exclusions')

        # Deleting model 'FacesStyleFiles'
        db.delete_table(u'faces_style_files')

        # Deleting model 'FacesStyleMeta'
        db.delete_table(u'faces_style_meta')

        # Deleting model 'FacesStyle'
        db.delete_table(u'faces_styles')

        # Deleting model 'FBObjectAttribute'
        db.delete_table(u'fb_object_attributes')

        # Deleting model 'FBObjectMeta'
        db.delete_table(u'fb_object_meta')

        # Deleting model 'FBObject'
        db.delete_table(u'fb_objects')

        # Deleting model 'FilterFeature'
        db.delete_table(u'filter_features')

        # Deleting model 'FilterMeta'
        db.delete_table(u'filter_meta')

        # Deleting model 'Filter'
        db.delete_table(u'filters')

        # Deleting model 'MixModelDefinition'
        db.delete_table(u'mix_model_definitions')

        # Deleting model 'MixModelMeta'
        db.delete_table(u'mix_model_meta')

        # Deleting model 'MixModel'
        db.delete_table(u'mix_models')

        # Deleting model 'PropensityModelDefinition'
        db.delete_table(u'propensity_model_definitions')

        # Deleting model 'PropensityModelMeta'
        db.delete_table(u'propensity_model_meta')

        # Deleting model 'PropensityModel'
        db.delete_table(u'propensity_models')

        # Deleting model 'ProximityModelDefinition'
        db.delete_table(u'proximity_model_definitions')

        # Deleting model 'ProximityModelMeta'
        db.delete_table(u'proximity_model_meta')

        # Deleting model 'ProximityModel'
        db.delete_table(u'proximity_models')

        # Deleting model 'ShareMessage'
        db.delete_table(u'share_messages')

        # Deleting model 'UserClient'
        db.delete_table(u'user_clients')


    models = {
        u'targetshare.assignment': {
            'Meta': {'object_name': 'Assignment', 'db_table': "u'assignments'"},
            'assign_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'chosen_from_rows': ('django.db.models.fields.CharField', [], {'max_length': '128L', 'blank': 'True'}),
            'chosen_from_table': ('django.db.models.fields.CharField', [], {'max_length': '128L', 'blank': 'True'}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ClientContent']", 'null': 'True', 'blank': 'True'}),
            'feature_row': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '128L', 'blank': 'True'}),
            'random_assign': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '128L', 'blank': 'True'})
        },
        u'targetshare.buttonstyle': {
            'Meta': {'object_name': 'ButtonStyle', 'db_table': "u'button_styles'"},
            'button_style_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'targetshare.buttonstylefile': {
            'Meta': {'object_name': 'ButtonStyleFile', 'db_table': "u'button_style_files'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ButtonStyle']", 'null': 'True', 'blank': 'True'}),
            'button_style_file_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'css_file': ('django.db.models.fields.CharField', [], {'max_length': '128L', 'blank': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'html_template': ('django.db.models.fields.CharField', [], {'max_length': '128L', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.buttonstylemeta': {
            'Meta': {'object_name': 'ButtonStyleMeta', 'db_table': "u'button_style_meta'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ButtonStyle']", 'null': 'True', 'blank': 'True'}),
            'button_style_meta_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'})
        },
        u'targetshare.campaign': {
            'Meta': {'object_name': 'Campaign', 'db_table': "u'campaigns'"},
            'campaign_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'targetshare.campaignbuttonstyle': {
            'Meta': {'object_name': 'CampaignButtonStyle', 'db_table': "u'campaign_button_styles'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ButtonStyle']", 'null': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_button_style_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.campaignchoiceset': {
            'Meta': {'object_name': 'CampaignChoiceSet', 'db_table': "u'campaign_choice_sets'"},
            'allow_generic': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_choice_set_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSet']", 'null': 'True', 'blank': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'generic_url_slug': ('django.db.models.fields.CharField', [], {'max_length': '64L', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.campaignchoicesetalgorithm': {
            'Meta': {'object_name': 'CampaignChoiceSetAlgorithm', 'db_table': "u'campaign_choice_set_algoritm'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_choice_set_algorithm_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True', 'db_column': "u'campaign_choice_set_algoritm_id'"}),
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSetAlgorithm']", 'null': 'True', 'db_column': "u'choice_set_algoritm_id'", 'blank': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.campaignfacesstyle': {
            'Meta': {'object_name': 'CampaignFacesStyle', 'db_table': "u'campaign_faces_styles'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_faces_style_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FacesStyle']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.campaignfbobjects': {
            'Meta': {'object_name': 'CampaignFBObjects', 'db_table': "u'campaign_fb_objects'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_fb_object_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FBObject']", 'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.campaigngenericfbobjects': {
            'Meta': {'object_name': 'CampaignGenericFbObjects', 'db_table': "u'campaign_generic_fb_objects'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_generic_fb_object_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FBObject']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.campaignglobalfilter': {
            'Meta': {'object_name': 'CampaignGlobalFilter', 'db_table': "u'campaign_global_filters'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_global_filter_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.campaignmeta': {
            'Meta': {'object_name': 'CampaignMeta', 'db_table': "u'campaign_meta'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_meta_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'})
        },
        u'targetshare.campaignmixmodel': {
            'Meta': {'object_name': 'CampaignMixModel', 'db_table': "u'campaign_mix_models'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_mix_model_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.MixModel']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.campaignpropensitymodel': {
            'Meta': {'object_name': 'CampaignPropensityModel', 'db_table': "u'campaign_propensity_models'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_propensity_model_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.PropensityModel']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.campaignproperties': {
            'Meta': {'object_name': 'CampaignProperties', 'db_table': "u'campaign_properties'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_property_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'client_error_url': ('django.db.models.fields.CharField', [], {'max_length': '2096L', 'blank': 'True'}),
            'client_faces_url': ('django.db.models.fields.CharField', [], {'max_length': '2096L', 'blank': 'True'}),
            'client_thanks_url': ('django.db.models.fields.CharField', [], {'max_length': '2096L', 'blank': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fallback_campaign': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'fallback'", 'null': 'True', 'to': u"orm['targetshare.Campaign']"}),
            'fallback_content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ClientContent']", 'null': 'True', 'blank': 'True'}),
            'fallback_is_cascading': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'min_friends': ('django.db.models.fields.IntegerField', [], {}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.campaignproximitymodel': {
            'Meta': {'object_name': 'CampaignProximityModel', 'db_table': "u'campaign_proximity_models'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_proximity_model_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ProximityModel']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.choiceset': {
            'Meta': {'object_name': 'ChoiceSet', 'db_table': "u'choice_sets'"},
            'choice_set_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'targetshare.choicesetalgorithm': {
            'Meta': {'object_name': 'ChoiceSetAlgorithm', 'db_table': "u'choice_set_algoritms'"},
            'choice_set_algorithm_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'targetshare.choicesetalgorithmdefinition': {
            'Meta': {'object_name': 'ChoiceSetAlgorithmDefinition', 'db_table': "u'choice_set_algoritm_definitions'"},
            'algorithm_definition': ('django.db.models.fields.CharField', [], {'max_length': '4096L', 'blank': 'True'}),
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSetAlgorithm']", 'null': 'True', 'db_column': "u'choice_set_algoritm_id'", 'blank': 'True'}),
            'choice_set_algorithm_definition_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True', 'db_column': "u'choice_set_algoritm_definition_id'"}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.choicesetalgorithmmeta': {
            'Meta': {'object_name': 'ChoiceSetAlgorithmMeta', 'db_table': "u'choice_set_algoritm_meta'"},
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSetAlgorithm']", 'null': 'True', 'db_column': "u'choice_set_algoritm_id'", 'blank': 'True'}),
            'choice_set_algorithm_meta_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True', 'db_column': "u'choice_set_algoritm_meta_id'"}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'})
        },
        u'targetshare.choicesetfilter': {
            'Meta': {'object_name': 'ChoiceSetFilter', 'db_table': "u'choice_set_filters'"},
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSet']", 'null': 'True', 'blank': 'True'}),
            'choice_set_filter_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'propensity_model_type': ('django.db.models.fields.CharField', [], {'max_length': '32L', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'url_slug': ('django.db.models.fields.CharField', [], {'max_length': '64L', 'blank': 'True'})
        },
        u'targetshare.choicesetmeta': {
            'Meta': {'object_name': 'ChoiceSetMeta', 'db_table': "u'choice_set_meta'"},
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSet']", 'null': 'True', 'blank': 'True'}),
            'choice_set_meta_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'})
        },
        u'targetshare.client': {
            'Meta': {'object_name': 'Client', 'db_table': "u'clients'"},
            'client_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'fb_app_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'fb_app_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'subdomain': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'targetshare.clientcontent': {
            'Meta': {'object_name': 'ClientContent', 'db_table': "u'client_content'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'content_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '2048L', 'blank': 'True'})
        },
        u'targetshare.clientdefault': {
            'Meta': {'object_name': 'ClientDefault', 'db_table': "u'client_defaults'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ButtonStyle']", 'null': 'True', 'blank': 'True'}),
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSet']", 'null': 'True', 'blank': 'True'}),
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ChoiceSetAlgorithm']", 'null': 'True', 'blank': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'client_default_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FacesStyle']", 'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.MixModel']", 'null': 'True', 'blank': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.PropensityModel']", 'null': 'True', 'blank': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ProximityModel']", 'null': 'True', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.event': {
            'Meta': {'object_name': 'Event', 'db_table': "u'events'"},
            'activity_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'app_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True', 'db_column': "u'appid'"}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'client_content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ClientContent']", 'null': 'True', 'db_column': "u'content_id'", 'blank': 'True'}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '128L', 'blank': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'friend_fbid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '32L', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '128L', 'blank': 'True'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '64L', 'blank': 'True', 'db_column': "u'type'"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.faceexclusion': {
            'Meta': {'object_name': 'FaceExclusion', 'db_table': "u'face_exclusions'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']"}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ClientContent']"}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {}),
            'friend_fbid': ('django.db.models.fields.BigIntegerField', [], {}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '512L', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.facesstyle': {
            'Meta': {'object_name': 'FacesStyle', 'db_table': "u'faces_styles'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'faces_style_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'targetshare.facesstylefiles': {
            'Meta': {'object_name': 'FacesStyleFiles', 'db_table': "u'faces_style_files'"},
            'css_file': ('django.db.models.fields.CharField', [], {'max_length': '128L', 'blank': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'faces_style_file_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'faces_style_id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FacesStyle']", 'null': 'True', 'blank': 'True'}),
            'html_template': ('django.db.models.fields.CharField', [], {'max_length': '128L', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.facesstylemeta': {
            'Meta': {'object_name': 'FacesStyleMeta', 'db_table': "u'faces_style_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FacesStyle']", 'null': 'True', 'blank': 'True'}),
            'faces_style_meta_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'})
        },
        u'targetshare.fbobject': {
            'Meta': {'object_name': 'FBObject', 'db_table': "u'fb_objects'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'fb_object_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'targetshare.fbobjectattribute': {
            'Meta': {'object_name': 'FBObjectAttribute', 'db_table': "u'fb_object_attributes'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FBObject']", 'null': 'True', 'blank': 'True'}),
            'fb_object_attributes_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'msg1_post': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'msg1_pre': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'msg2_post': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'msg2_pre': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'og_action': ('django.db.models.fields.CharField', [], {'max_length': '64L', 'blank': 'True'}),
            'og_description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'og_image': ('django.db.models.fields.CharField', [], {'max_length': '2096L', 'blank': 'True'}),
            'og_title': ('django.db.models.fields.CharField', [], {'max_length': '128L', 'blank': 'True'}),
            'og_type': ('django.db.models.fields.CharField', [], {'max_length': '64L', 'blank': 'True'}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'sharing_prompt': ('django.db.models.fields.CharField', [], {'max_length': '2096L', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'url_slug': ('django.db.models.fields.CharField', [], {'max_length': '64L', 'blank': 'True'})
        },
        u'targetshare.fbobjectmeta': {
            'Meta': {'object_name': 'FBObjectMeta', 'db_table': "u'fb_object_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.FBObject']", 'null': 'True', 'blank': 'True'}),
            'fb_object_meta_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'})
        },
        u'targetshare.filter': {
            'Meta': {'object_name': 'Filter', 'db_table': "u'filters'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'filter_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'targetshare.filterfeature': {
            'Meta': {'object_name': 'FilterFeature', 'db_table': "u'filter_features'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'feature': ('django.db.models.fields.CharField', [], {'max_length': '64L', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'filter_feature_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'operator': ('django.db.models.fields.CharField', [], {'max_length': '32L', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'value_type': ('django.db.models.fields.CharField', [], {'max_length': '32L', 'blank': 'True'})
        },
        u'targetshare.filtermeta': {
            'Meta': {'object_name': 'FilterMeta', 'db_table': "u'filter_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'filter_meta_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'})
        },
        u'targetshare.mixmodel': {
            'Meta': {'object_name': 'MixModel', 'db_table': "u'mix_models'"},
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mix_model_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'targetshare.mixmodeldefinition': {
            'Meta': {'object_name': 'MixModelDefinition', 'db_table': "u'mix_model_definitions'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.MixModel']", 'null': 'True', 'blank': 'True'}),
            'mix_model_definition_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'model_definition': ('django.db.models.fields.CharField', [], {'max_length': '4096L', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.mixmodelmeta': {
            'Meta': {'object_name': 'MixModelMeta', 'db_table': "u'mix_model_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.MixModel']", 'null': 'True', 'blank': 'True'}),
            'mix_model_meta_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'})
        },
        u'targetshare.propensitymodel': {
            'Meta': {'object_name': 'PropensityModel', 'db_table': "u'propensity_models'"},
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'proximity_model_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        },
        u'targetshare.propensitymodeldefinition': {
            'Meta': {'object_name': 'PropensityModelDefinition', 'db_table': "u'propensity_model_definitions'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'model_definition': ('django.db.models.fields.CharField', [], {'max_length': '4096L', 'blank': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.PropensityModel']", 'null': 'True', 'blank': 'True'}),
            'propensity_model_definition_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'propensity_model_type': ('django.db.models.fields.CharField', [], {'max_length': '64L', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.propensitymodelmeta': {
            'Meta': {'object_name': 'PropensityModelMeta', 'db_table': "u'propensity_model_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.PropensityModel']", 'null': 'True', 'blank': 'True'}),
            'propensity_model_meta_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'})
        },
        u'targetshare.proximitymodel': {
            'Meta': {'object_name': 'ProximityModel', 'db_table': "u'proximity_models'"},
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'proximity_model_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        },
        u'targetshare.proximitymodeldefinition': {
            'Meta': {'object_name': 'ProximityModelDefinition', 'db_table': "u'proximity_model_definitions'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'model_definition': ('django.db.models.fields.CharField', [], {'max_length': '4096L', 'blank': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ProximityModel']", 'null': 'True', 'blank': 'True'}),
            'proximity_model_definition_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.proximitymodelmeta': {
            'Meta': {'object_name': 'ProximityModelMeta', 'db_table': "u'proximity_model_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ProximityModel']", 'null': 'True', 'blank': 'True'}),
            'proximity_model_meta_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024L', 'blank': 'True'})
        },
        u'targetshare.sharemessage': {
            'Meta': {'object_name': 'ShareMessage', 'db_table': "u'share_messages'"},
            'activity_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ClientContent']", 'null': 'True', 'blank': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '4096L', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'targetshare.userclient': {
            'Meta': {'object_name': 'UserClient', 'db_table': "u'user_clients'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {}),
        }
    }

    complete_apps = ['targetshare']
