# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration
from django.conf import settings

DB_NAME = settings.DATABASES['default']['NAME']
PRIMARY_KEY_SQL = """
    select constraint_name from information_schema.table_constraints
    where table_name = '%s'
    and table_schema = '%s'
    and constraint_name = 'PRIMARY'
    """


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Changing field 'FBObjectMeta.name'
        db.alter_column('fb_object_meta', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=128))

        # Changing field 'FBObjectMeta.value'
        db.alter_column('fb_object_meta', 'value', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'FBObjectMeta.fb_object_meta_id'
        db.alter_column('fb_object_meta', 'fb_object_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'FBObjectMeta.start_dt'
        db.alter_column('fb_object_meta', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Filter.create_dt'
        db.alter_column('filters', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Filter.is_deleted'
        db.alter_column('filters', 'is_deleted', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'Filter.description'
        db.alter_column('filters', 'description', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'Filter.filter_id'
        db.alter_column('filters', 'filter_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'Filter.name'
        db.alter_column('filters', 'name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True))

        # Changing field 'PropensityModelMeta.propensity_model_meta_id'
        db.alter_column('propensity_model_meta', 'propensity_model_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'PropensityModelMeta.name'
        db.alter_column('propensity_model_meta', 'name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True))

        # Changing field 'PropensityModelMeta.value'
        db.alter_column('propensity_model_meta', 'value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True))

        # Changing field 'PropensityModelMeta.start_dt'
        db.alter_column('propensity_model_meta', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ChoiceSetAlgorithmMeta.name'
        db.alter_column('choice_set_algoritm_meta', 'name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True))

        # Changing field 'ChoiceSetAlgorithmMeta.choice_set_algorithm_meta_id'
        db.alter_column('choice_set_algoritm_meta', 'choice_set_algoritm_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True, db_column='choice_set_algoritm_meta_id'))

        # Changing field 'ChoiceSetAlgorithmMeta.value'
        db.alter_column('choice_set_algoritm_meta', 'value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True))

        # Changing field 'ChoiceSetAlgorithmMeta.choice_set_algorithm'
        db.alter_column('choice_set_algoritm_meta', 'choice_set_algoritm_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSetAlgorithm'], null=True, db_column='choice_set_algoritm_id'))

        # Changing field 'ChoiceSetAlgorithmMeta.start_dt'
        db.alter_column('choice_set_algoritm_meta', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ButtonStyleMeta.name'
        db.alter_column('button_style_meta', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'ButtonStyleMeta.value'
        db.alter_column('button_style_meta', 'value', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'ButtonStyleMeta.button_style_meta_id'
        db.alter_column('button_style_meta', 'button_style_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ButtonStyleMeta.start_dt'
        db.alter_column('button_style_meta', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'CampaignMeta.name'
        db.alter_column('campaign_meta', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'CampaignMeta.value'
        db.alter_column('campaign_meta', 'value', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'CampaignMeta.start_dt'
        db.alter_column('campaign_meta', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'CampaignMeta.campaign_meta_id'
        db.alter_column('campaign_meta', 'campaign_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'CampaignChoiceSet.generic_url_slug'
        db.alter_column('campaign_choice_sets', 'generic_url_slug', self.gf('django.db.models.fields.CharField')(max_length=64, null=True))

        # Changing field 'CampaignChoiceSet.allow_generic'
        db.alter_column('campaign_choice_sets', 'allow_generic', self.gf('django.db.models.fields.NullBooleanField')(null=True))

        # Changing field 'CampaignChoiceSet.rand_cdf'
        db.alter_column('campaign_choice_sets', 'rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=9))

        # Changing field 'CampaignChoiceSet.campaign_choice_set_id'
        db.alter_column('campaign_choice_sets', 'campaign_choice_set_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'CampaignChoiceSet.start_dt'
        db.alter_column('campaign_choice_sets', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'CampaignProperties.fallback_is_cascading'
        db.alter_column('campaign_properties', 'fallback_is_cascading', self.gf('django.db.models.fields.NullBooleanField')(null=True))

        # Changing field 'CampaignProperties.client_thanks_url'
        db.alter_column('campaign_properties', 'client_thanks_url', self.gf('django.db.models.fields.CharField')(default='', max_length=2096))

        # Changing field 'CampaignProperties.campaign_property_id'
        db.alter_column('campaign_properties', 'campaign_property_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'CampaignProperties.client_faces_url'
        db.alter_column('campaign_properties', 'client_faces_url', self.gf('django.db.models.fields.CharField')(default='', max_length=2096))

        # Changing field 'CampaignProperties.client_error_url'
        db.alter_column('campaign_properties', 'client_error_url', self.gf('django.db.models.fields.CharField')(default='', max_length=2096))

        # Changing field 'CampaignProperties.start_dt'
        db.alter_column('campaign_properties', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'FilterFeature.filter_feature_id'
        db.alter_column('filter_features', 'filter_feature_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'FilterFeature.feature'
        db.alter_column('filter_features', 'feature', self.gf('django.db.models.fields.CharField')(default='', max_length=64))

        # Changing field 'FilterFeature.value'
        db.alter_column('filter_features', 'value', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'FilterFeature.value_type'
        db.alter_column('filter_features', 'value_type', self.gf('django.db.models.fields.CharField')(default='', max_length=32))

        # Changing field 'FilterFeature.operator'
        db.alter_column('filter_features', 'operator', self.gf('django.db.models.fields.CharField')(default='', max_length=32))

        # Changing field 'FilterFeature.start_dt'
        db.alter_column('filter_features', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ChoiceSetAlgorithmDefinition.choice_set_algorithm_definition_id'
        db.alter_column('choice_set_algoritm_definitions', 'choice_set_algoritm_definition_id', self.gf('django.db.models.fields.AutoField')(primary_key=True, db_column='choice_set_algoritm_definition_id'))

        # Changing field 'ChoiceSetAlgorithmDefinition.algorithm_definition'
        db.alter_column('choice_set_algoritm_definitions', 'algorithm_definition', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'ChoiceSetAlgorithmDefinition.start_dt'
        db.alter_column('choice_set_algoritm_definitions', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ChoiceSetAlgorithmDefinition.choice_set_algorithm'
        db.alter_column('choice_set_algoritm_definitions', 'choice_set_algoritm_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSetAlgorithm'], null=True, db_column='choice_set_algoritm_id'))

        # Changing field 'FacesStyleMeta.name'
        db.alter_column('faces_style_meta', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=128))

        # Changing field 'FacesStyleMeta.faces_style_meta_id'
        db.alter_column('faces_style_meta', 'faces_style_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'FacesStyleMeta.value'
        db.alter_column('faces_style_meta', 'value', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'FacesStyleMeta.start_dt'
        db.alter_column('faces_style_meta', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Event primary key
        db.execute('ALTER TABLE events ADD event_id MEDIUMINT NOT NULL AUTO_INCREMENT KEY')

        # Changing field 'Event.ip'
        db.alter_column('events', 'ip', self.gf('django.db.models.fields.CharField')(default='', max_length=32))

        # Changing field 'Event.updated'
        db.alter_column('events', 'updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'Event.session_id'
        db.alter_column('events', 'session_id', self.gf('django.db.models.fields.CharField')(default='', max_length=128))

        # Changing field 'Event.content'
        db.alter_column('events', 'content', self.gf('django.db.models.fields.CharField')(default='', max_length=128))

        # Changing field 'Event.client_content'
        db.alter_column('events', 'content_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ClientContent'], null=True, db_column='content_id'))

        # Changing field 'FBObjectAttribute.og_image'
        db.alter_column('fb_object_attributes', 'og_image', self.gf('django.db.models.fields.CharField')(default='', max_length=2096))

        # Changing field 'FBObjectAttribute.fb_object_attributes_id'
        db.alter_column('fb_object_attributes', 'fb_object_attributes_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'FBObjectAttribute.og_description'
        db.alter_column('fb_object_attributes', 'og_description', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'FBObjectAttribute.page_title'
        db.alter_column('fb_object_attributes', 'page_title', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'FBObjectAttribute.msg2_pre'
        db.alter_column('fb_object_attributes', 'msg2_pre', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'FBObjectAttribute.msg1_post'
        db.alter_column('fb_object_attributes', 'msg1_post', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'FBObjectAttribute.og_action'
        db.alter_column('fb_object_attributes', 'og_action', self.gf('django.db.models.fields.CharField')(default='', max_length=64))

        # Changing field 'FBObjectAttribute.og_type'
        db.alter_column('fb_object_attributes', 'og_type', self.gf('django.db.models.fields.CharField')(default='', max_length=64))

        # Changing field 'FBObjectAttribute.msg1_pre'
        db.alter_column('fb_object_attributes', 'msg1_pre', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'FBObjectAttribute.sharing_prompt'
        db.alter_column('fb_object_attributes', 'sharing_prompt', self.gf('django.db.models.fields.CharField')(default='', max_length=2096))

        # Changing field 'FBObjectAttribute.msg2_post'
        db.alter_column('fb_object_attributes', 'msg2_post', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'FBObjectAttribute.og_title'
        db.alter_column('fb_object_attributes', 'og_title', self.gf('django.db.models.fields.CharField')(default='', max_length=128))

        # Changing field 'FBObjectAttribute.start_dt'
        db.alter_column('fb_object_attributes', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'FBObjectAttribute.url_slug'
        db.alter_column('fb_object_attributes', 'url_slug', self.gf('django.db.models.fields.CharField')(default='', max_length=64))

        # Changing field 'ChoiceSet.create_dt'
        db.alter_column('choice_sets', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ChoiceSet.is_deleted'
        db.alter_column('choice_sets', 'is_deleted', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'ChoiceSet.name'
        db.alter_column('choice_sets', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'ChoiceSet.choice_set_id'
        db.alter_column('choice_sets', 'choice_set_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ChoiceSet.description'
        db.alter_column('choice_sets', 'description', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'ShareMessage.updated'
        db.alter_column('share_messages', 'updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'ShareMessage.message'
        db.alter_column('share_messages', 'message', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'CampaignFBObjects.campaign_fb_object_id'
        db.alter_column('campaign_fb_objects', 'campaign_fb_object_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'CampaignFBObjects.rand_cdf'
        db.alter_column('campaign_fb_objects', 'rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=9))

        # Changing field 'CampaignFBObjects.start_dt'
        db.alter_column('campaign_fb_objects', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'CampaignGlobalFilter.rand_cdf'
        db.alter_column('campaign_global_filters', 'rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=9))

        # Changing field 'CampaignGlobalFilter.campaign_global_filter_id'
        db.alter_column('campaign_global_filters', 'campaign_global_filter_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'CampaignGlobalFilter.start_dt'
        db.alter_column('campaign_global_filters', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'CampaignButtonStyle.campaign_button_style_id'
        db.alter_column('campaign_button_styles', 'campaign_button_style_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'CampaignButtonStyle.rand_cdf'
        db.alter_column('campaign_button_styles', 'rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=9))

        # Changing field 'CampaignButtonStyle.start_dt'
        db.alter_column('campaign_button_styles', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ChoiceSetAlgorithm.create_dt'
        db.alter_column('choice_set_algoritms', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ChoiceSetAlgorithm.is_deleted'
        db.alter_column('choice_set_algoritms', 'is_deleted', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'ChoiceSetAlgorithm.description'
        db.alter_column('choice_set_algoritms', 'description', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'ChoiceSetAlgorithm.name'
        db.alter_column('choice_set_algoritms', 'name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True))

        # Changing field 'ChoiceSetAlgorithm.choice_set_algorithm_id'
        db.alter_column('choice_set_algoritms', 'choice_set_algorithm_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ChoiceSetMeta.name'
        db.alter_column('choice_set_meta', 'name', self.gf('django.db.models.fields.CharField')(max_length=256))

        # Changing field 'ChoiceSetMeta.choice_set_meta_id'
        db.alter_column('choice_set_meta', 'choice_set_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ChoiceSetMeta.value'
        db.alter_column('choice_set_meta', 'value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True))

        # Changing field 'ChoiceSetMeta.start_dt'
        db.alter_column('choice_set_meta', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'PropensityModel.create_dt'
        db.alter_column('propensity_models', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'PropensityModel.is_deleted'
        db.alter_column('propensity_models', 'is_deleted', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'PropensityModel.description'
        db.alter_column('propensity_models', 'description', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True))

        # Changing field 'PropensityModel.proximity_model_id'
        db.alter_column('propensity_models', 'proximity_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'PropensityModel.name'
        db.alter_column('propensity_models', 'name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True))

        # Changing field 'ProximityModelMeta.name'
        db.alter_column('proximity_model_meta', 'name', self.gf('django.db.models.fields.CharField')(max_length=256))

        # Changing field 'ProximityModelMeta.value'
        db.alter_column('proximity_model_meta', 'value', self.gf('django.db.models.fields.CharField')(max_length=1024))

        # Changing field 'ProximityModelMeta.proximity_model_meta_id'
        db.alter_column('proximity_model_meta', 'proximity_model_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ProximityModelMeta.start_dt'
        db.alter_column('proximity_model_meta', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ProximityModelDefinition.proximity_model_definition_id'
        db.alter_column('proximity_model_definitions', 'proximity_model_definition_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ProximityModelDefinition.start_dt'
        db.alter_column('proximity_model_definitions', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ProximityModelDefinition.model_definition'
        db.alter_column('proximity_model_definitions', 'model_definition', self.gf('django.db.models.fields.TextField')())

        # Changing field 'ClientDefault.client_default_id'
        db.alter_column('client_defaults', 'client_default_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ClientDefault.start_dt'
        db.alter_column('client_defaults', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'MixModelDefinition.start_dt'
        db.alter_column('mix_model_definitions', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'MixModelDefinition.model_definition'
        db.alter_column('mix_model_definitions', 'model_definition', self.gf('django.db.models.fields.TextField')())

        # Changing field 'MixModelDefinition.mix_model_definition_id'
        db.alter_column('mix_model_definitions', 'mix_model_definition_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Adding field 'Assignment.assignment_id'
        db.execute('ALTER TABLE assignments ADD assignment_id MEDIUMINT NOT NULL AUTO_INCREMENT KEY')

        # Changing field 'Assignment.chosen_from_rows'
        db.alter_column('assignments', 'chosen_from_rows', self.gf('django.db.models.fields.CharField')(max_length=128))

        # Changing field 'Assignment.feature_type'
        db.alter_column('assignments', 'feature_type', self.gf('django.db.models.fields.CharField')(max_length=128))

        # Changing field 'Assignment.session_id'
        db.alter_column('assignments', 'session_id', self.gf('django.db.models.fields.CharField')(max_length=128))

        # Changing field 'Assignment.assign_dt'
        db.alter_column('assignments', 'assign_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Assignment.chosen_from_table'
        db.alter_column('assignments', 'chosen_from_table', self.gf('django.db.models.fields.CharField')(max_length=128))

        # Changing field 'Assignment.random_assign'
        db.alter_column('assignments', 'random_assign', self.gf('django.db.models.fields.NullBooleanField')(null=True))

        # Changing field 'ProximityModel.create_dt'
        db.alter_column('proximity_models', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ProximityModel.is_deleted'
        db.alter_column('proximity_models', 'is_deleted', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'ProximityModel.description'
        db.alter_column('proximity_models', 'description', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True))

        # Changing field 'ProximityModel.proximity_model_id'
        db.alter_column('proximity_models', 'proximity_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ProximityModel.name'
        db.alter_column('proximity_models', 'name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True))

        # Changing field 'CampaignFacesStyle.campaign_faces_style_id'
        db.alter_column('campaign_faces_styles', 'campaign_faces_style_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'CampaignFacesStyle.rand_cdf'
        db.alter_column('campaign_faces_styles', 'rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=9))

        # Changing field 'CampaignFacesStyle.start_dt'
        db.alter_column('campaign_faces_styles', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ButtonStyleFile.button_style_file_id'
        db.alter_column('button_style_files', 'button_style_file_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ButtonStyleFile.css_file'
        db.alter_column('button_style_files', 'css_file', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'ButtonStyleFile.start_dt'
        db.alter_column('button_style_files', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ButtonStyleFile.html_template'
        db.alter_column('button_style_files', 'html_template', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'CampaignPropensityModel.campaign_propensity_model_id'
        db.alter_column('campaign_propensity_models', 'campaign_propensity_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'CampaignPropensityModel.rand_cdf'
        db.alter_column('campaign_propensity_models', 'rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=9))

        # Changing field 'CampaignPropensityModel.start_dt'
        db.alter_column('campaign_propensity_models', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'MixModel.create_dt'
        db.alter_column('mix_models', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'MixModel.is_deleted'
        db.alter_column('mix_models', 'is_deleted', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'MixModel.description'
        db.alter_column('mix_models', 'description', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True))

        # Changing field 'MixModel.mix_model_id'
        db.alter_column('mix_models', 'mix_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'MixModel.name'
        db.alter_column('mix_models', 'name', self.gf('django.db.models.fields.CharField')(max_length=256, null=True))

        # Changing field 'Campaign.create_dt'
        db.alter_column('campaigns', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Campaign.is_deleted'
        db.alter_column('campaigns', 'is_deleted', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'Campaign.description'
        db.alter_column('campaigns', 'description', self.gf('django.db.models.fields.TextField')(default=''))

        # Changing field 'Campaign.campaign_id'
        db.alter_column('campaigns', 'campaign_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'Campaign.name'
        db.alter_column('campaigns', 'name', self.gf('django.db.models.fields.CharField')(max_length=256))

        # Changing field 'FilterMeta.name'
        db.alter_column('filter_meta', 'name', self.gf('django.db.models.fields.CharField')(max_length=128))

        # Changing field 'FilterMeta.value'
        db.alter_column('filter_meta', 'value', self.gf('django.db.models.fields.CharField')(max_length=1024))

        # Changing field 'FilterMeta.filter_meta_id'
        db.alter_column('filter_meta', 'filter_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'FilterMeta.start_dt'
        db.alter_column('filter_meta', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Face Exclusion primary key
        if db.execute(PRIMARY_KEY_SQL % ('face_exclusions', DB_NAME)):
            db.execute('ALTER TABLE face_exclusions DROP PRIMARY KEY')
        db.execute('ALTER TABLE face_exclusions ADD face_exclusion_id MEDIUMINT NOT NULL AUTO_INCREMENT KEY')

        # Changing field 'FaceExclusion.updated'
        db.alter_column('face_exclusions', 'updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))

        # Changing field 'FaceExclusion.reason'
        db.alter_column('face_exclusions', 'reason', self.gf('django.db.models.fields.CharField')(max_length=512, null=True))
        # Adding unique constraint on 'FaceExclusion', fields ['content', 'fbid', 'campaign', 'friend_fbid']
        db.create_unique('face_exclusions', ['content_id', 'fbid', 'campaign_id', 'friend_fbid'])

        # Changing field 'CampaignGenericFBObjects.campaign_generic_fb_object_id'
        db.alter_column('campaign_generic_fb_objects', 'campaign_generic_fb_object_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'CampaignGenericFBObjects.rand_cdf'
        db.alter_column('campaign_generic_fb_objects', 'rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=9))

        # Changing field 'CampaignGenericFBObjects.start_dt'
        db.alter_column('campaign_generic_fb_objects', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ClientContent.create_dt'
        db.alter_column('client_content', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ClientContent.is_deleted'
        db.alter_column('client_content', 'is_deleted', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'ClientContent.description'
        db.alter_column('client_content', 'description', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'ClientContent.url'
        db.alter_column('client_content', 'url', self.gf('django.db.models.fields.CharField')(default='', max_length=2048))

        # Changing field 'ClientContent.content_id'
        db.alter_column('client_content', 'content_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ClientContent.name'
        db.alter_column('client_content', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Renaming column for 'CampaignChoiceSetAlgorithm.campaign_choice_set_algorithm_id' to match new field type.
        db.rename_column('campaign_choice_set_algoritm', u'campaign_choice_set_algoritm_id', 'campaign_choice_set_algorithm_id')
        # Changing field 'CampaignChoiceSetAlgorithm.campaign_choice_set_algorithm_id'
        db.alter_column('campaign_choice_set_algoritm', 'campaign_choice_set_algorithm_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'CampaignChoiceSetAlgorithm.choice_set_algorithm'
        db.alter_column('campaign_choice_set_algoritm', 'choice_set_algoritm_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.ChoiceSetAlgorithm'], null=True, db_column='choice_set_algoritm_id'))

        # Changing field 'CampaignChoiceSetAlgorithm.rand_cdf'
        db.alter_column('campaign_choice_set_algoritm', 'rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=9))

        # Changing field 'CampaignChoiceSetAlgorithm.start_dt'
        db.alter_column('campaign_choice_set_algoritm', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Client.domain'
        db.alter_column('clients', 'domain', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'Client.fb_app_name'
        db.alter_column('clients', 'fb_app_name', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'Client.create_dt'
        db.alter_column('clients', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'Client.name'
        db.alter_column('clients', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=255))

        # Changing field 'Client.client_id'
        db.alter_column('clients', 'client_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'Client.subdomain'
        db.alter_column('clients', 'subdomain', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'Client.fb_app_id'
        db.alter_column('clients', 'fb_app_id', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'FacesStyleFiles.css_file'
        db.alter_column('faces_style_files', 'css_file', self.gf('django.db.models.fields.CharField')(default='', max_length=128))

        # Changing field 'FacesStyleFiles.start_dt'
        db.alter_column('faces_style_files', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'FacesStyleFiles.faces_style_file_id'
        db.alter_column('faces_style_files', 'faces_style_file_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'FacesStyleFiles.html_template'
        db.alter_column('faces_style_files', 'html_template', self.gf('django.db.models.fields.CharField')(default='', max_length=128))

        # Changing field 'CampaignMixModel.campaign_mix_model_id'
        db.alter_column('campaign_mix_models', 'campaign_mix_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'CampaignMixModel.rand_cdf'
        db.alter_column('campaign_mix_models', 'rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=9))

        # Changing field 'CampaignMixModel.start_dt'
        db.alter_column('campaign_mix_models', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'CampaignProximityModel.rand_cdf'
        db.alter_column('campaign_proximity_models', 'rand_cdf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=9))

        # Changing field 'CampaignProximityModel.start_dt'
        db.alter_column('campaign_proximity_models', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'CampaignProximityModel.campaign_proximity_model_id'
        db.alter_column('campaign_proximity_models', 'campaign_proximity_model_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ButtonStyle.button_style_id'
        db.alter_column('button_styles', 'button_style_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ButtonStyle.create_dt'
        db.alter_column('button_styles', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ButtonStyle.is_deleted'
        db.alter_column('button_styles', 'is_deleted', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'ButtonStyle.name'
        db.alter_column('button_styles', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'ButtonStyle.description'
        db.alter_column('button_styles', 'description', self.gf('django.db.models.fields.TextField')(null=True))

        # User Client Primary Key
        if db.execute(PRIMARY_KEY_SQL % ('user_clients', DB_NAME)):
            db.execute('ALTER TABLE user_clients DROP PRIMARY KEY')
        db.execute('ALTER TABLE user_clients ADD user_client_id MEDIUMINT NOT NULL AUTO_INCREMENT KEY')

        # Changing field 'UserClient.create_dt'
        db.alter_column('user_clients', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))
        # Adding unique constraint on 'UserClient', fields ['fbid', 'client']
        db.create_unique('user_clients', ['fbid', 'client_id'])

        # Changing field 'FBObject.create_dt'
        db.alter_column('fb_objects', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'FBObject.is_deleted'
        db.alter_column('fb_objects', 'is_deleted', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'FBObject.name'
        db.alter_column('fb_objects', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'FBObject.fb_object_id'
        db.alter_column('fb_objects', 'fb_object_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'FBObject.description'
        db.alter_column('fb_objects', 'description', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'ChoiceSetFilter.propensity_model_type'
        db.alter_column('choice_set_filters', 'propensity_model_type', self.gf('django.db.models.fields.CharField')(default='', max_length=32))

        # Changing field 'ChoiceSetFilter.choice_set_filter_id'
        db.alter_column('choice_set_filters', 'choice_set_filter_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'ChoiceSetFilter.start_dt'
        db.alter_column('choice_set_filters', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'ChoiceSetFilter.url_slug'
        db.alter_column('choice_set_filters', 'url_slug', self.gf('django.db.models.fields.CharField')(default='', max_length=64))

        # Changing field 'FacesStyle.create_dt'
        db.alter_column('faces_styles', 'create_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'FacesStyle.is_deleted'
        db.alter_column('faces_styles', 'is_deleted', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'FacesStyle.name'
        db.alter_column('faces_styles', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'FacesStyle.faces_style_id'
        db.alter_column('faces_styles', 'faces_style_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'FacesStyle.description'
        db.alter_column('faces_styles', 'description', self.gf('django.db.models.fields.TextField')(null=True))

        # Changing field 'MixModelMeta.name'
        db.alter_column('mix_model_meta', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=256))

        # Changing field 'MixModelMeta.value'
        db.alter_column('mix_model_meta', 'value', self.gf('django.db.models.fields.CharField')(default='', max_length=1024))

        # Changing field 'MixModelMeta.mix_model_meta_id'
        db.alter_column('mix_model_meta', 'mix_model_meta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'MixModelMeta.start_dt'
        db.alter_column('mix_model_meta', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'PropensityModelDefinition.propensity_model_type'
        db.alter_column('propensity_model_definitions', 'propensity_model_type', self.gf('django.db.models.fields.CharField')(default='', max_length=64))

        # Changing field 'PropensityModelDefinition.propensity_model_definition_id'
        db.alter_column('propensity_model_definitions', 'propensity_model_definition_id', self.gf('django.db.models.fields.AutoField')(primary_key=True))

        # Changing field 'PropensityModelDefinition.start_dt'
        db.alter_column('propensity_model_definitions', 'start_dt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

        # Changing field 'PropensityModelDefinition.model_definition'
        db.alter_column('propensity_model_definitions', 'model_definition', self.gf('django.db.models.fields.TextField')())

    def backwards(self, orm):
        raise RuntimeError("Leave the past in the past")

    models = {
        'targetshare.assignment': {
            'Meta': {'object_name': 'Assignment', 'db_table': "'assignments'"},
            'assign_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'assignment_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'chosen_from_rows': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'chosen_from_table': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ClientContent']", 'null': 'True', 'blank': 'True'}),
            'feature_row': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'random_assign': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        'targetshare.buttonstyle': {
            'Meta': {'object_name': 'ButtonStyle', 'db_table': "'button_styles'"},
            'button_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        'targetshare.buttonstylefile': {
            'Meta': {'object_name': 'ButtonStyleFile', 'db_table': "'button_style_files'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ButtonStyle']", 'null': 'True', 'blank': 'True'}),
            'button_style_file_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'css_file': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'html_template': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.buttonstylemeta': {
            'Meta': {'object_name': 'ButtonStyleMeta', 'db_table': "'button_style_meta'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ButtonStyle']", 'null': 'True'}),
            'button_style_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'targetshare.campaign': {
            'Meta': {'object_name': 'Campaign', 'db_table': "'campaigns'"},
            'campaign_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        'targetshare.campaignbuttonstyle': {
            'Meta': {'object_name': 'CampaignButtonStyle', 'db_table': "'campaign_button_styles'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ButtonStyle']", 'null': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_button_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignchoiceset': {
            'Meta': {'object_name': 'CampaignChoiceSet', 'db_table': "'campaign_choice_sets'"},
            'allow_generic': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True'}),
            'campaign_choice_set_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ChoiceSet']", 'null': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'generic_url_slug': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignchoicesetalgorithm': {
            'Meta': {'object_name': 'CampaignChoiceSetAlgorithm', 'db_table': "'campaign_choice_set_algoritm'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_choice_set_algorithm_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ChoiceSetAlgorithm']", 'null': 'True', 'db_column': "'choice_set_algoritm_id'", 'blank': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignfacesstyle': {
            'Meta': {'object_name': 'CampaignFacesStyle', 'db_table': "'campaign_faces_styles'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_faces_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.FacesStyle']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignfbobjects': {
            'Meta': {'object_name': 'CampaignFBObjects', 'db_table': "'campaign_fb_objects'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_fb_object_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.FBObject']", 'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaigngenericfbobjects': {
            'Meta': {'object_name': 'CampaignGenericFBObjects', 'db_table': "'campaign_generic_fb_objects'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_generic_fb_object_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.FBObject']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignglobalfilter': {
            'Meta': {'object_name': 'CampaignGlobalFilter', 'db_table': "'campaign_global_filters'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_global_filter_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignmeta': {
            'Meta': {'object_name': 'CampaignMeta', 'db_table': "'campaign_meta'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True'}),
            'campaign_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'targetshare.campaignmixmodel': {
            'Meta': {'object_name': 'CampaignMixModel', 'db_table': "'campaign_mix_models'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_mix_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.MixModel']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignpropensitymodel': {
            'Meta': {'object_name': 'CampaignPropensityModel', 'db_table': "'campaign_propensity_models'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_propensity_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.PropensityModel']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignproperties': {
            'Meta': {'object_name': 'CampaignProperties', 'db_table': "'campaign_properties'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True'}),
            'campaign_property_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'client_error_url': ('django.db.models.fields.CharField', [], {'max_length': '2096'}),
            'client_faces_url': ('django.db.models.fields.CharField', [], {'max_length': '2096'}),
            'client_thanks_url': ('django.db.models.fields.CharField', [], {'max_length': '2096'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'fallback_campaign': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fallback_campaign'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'fallback_content': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ClientContent']", 'null': 'True'}),
            'fallback_is_cascading': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'min_friends': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignproximitymodel': {
            'Meta': {'object_name': 'CampaignProximityModel', 'db_table': "'campaign_proximity_models'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'campaign_proximity_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ProximityModel']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.choiceset': {
            'Meta': {'object_name': 'ChoiceSet', 'db_table': "'choice_sets'"},
            'choice_set_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        'targetshare.choicesetalgorithm': {
            'Meta': {'object_name': 'ChoiceSetAlgorithm', 'db_table': "'choice_set_algoritms'"},
            'choice_set_algorithm_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'})
        },
        'targetshare.choicesetalgorithmdefinition': {
            'Meta': {'object_name': 'ChoiceSetAlgorithmDefinition', 'db_table': "'choice_set_algoritm_definitions'"},
            'algorithm_definition': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ChoiceSetAlgorithm']", 'null': 'True', 'db_column': "'choice_set_algoritm_id'"}),
            'choice_set_algorithm_definition_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'db_column': "'choice_set_algoritm_definition_id'"}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.choicesetalgorithmmeta': {
            'Meta': {'object_name': 'ChoiceSetAlgorithmMeta', 'db_table': "'choice_set_algoritm_meta'"},
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ChoiceSetAlgorithm']", 'null': 'True', 'db_column': "'choice_set_algoritm_id'"}),
            'choice_set_algorithm_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True', 'db_column': "'choice_set_algoritm_meta_id'"}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        'targetshare.choicesetfilter': {
            'Meta': {'object_name': 'ChoiceSetFilter', 'db_table': "'choice_set_filters'"},
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ChoiceSet']", 'null': 'True', 'blank': 'True'}),
            'choice_set_filter_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'propensity_model_type': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'url_slug': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        },
        'targetshare.choicesetmeta': {
            'Meta': {'object_name': 'ChoiceSetMeta', 'db_table': "'choice_set_meta'"},
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ChoiceSet']", 'null': 'True', 'blank': 'True'}),
            'choice_set_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        'targetshare.client': {
            'Meta': {'object_name': 'Client', 'db_table': "'clients'"},
            'client_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'fb_app_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'fb_app_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'unique': 'True', 'blank': 'True'}),
            'subdomain': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        'targetshare.clientcontent': {
            'Meta': {'object_name': 'ClientContent', 'db_table': "'client_content'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'content_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'blank': 'True'})
        },
        'targetshare.clientdefault': {
            'Meta': {'object_name': 'ClientDefault', 'db_table': "'client_defaults'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ButtonStyle']", 'null': 'True', 'blank': 'True'}),
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ChoiceSet']", 'null': 'True', 'blank': 'True'}),
            'choice_set_algorithm': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ChoiceSetAlgorithm']", 'null': 'True', 'blank': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'client_default_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.FacesStyle']", 'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.MixModel']", 'null': 'True', 'blank': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.PropensityModel']", 'null': 'True', 'blank': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ProximityModel']", 'null': 'True', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.event': {
            'Meta': {'object_name': 'Event', 'db_table': "'events'"},
            'activity_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'app_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'db_column': "'appid'", 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True'}),
            'client_content': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ClientContent']", 'null': 'True', 'db_column': "'content_id'"}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'event_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'db_column': "'type'", 'blank': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'friend_fbid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'targetshare.faceexclusion': {
            'Meta': {'unique_together': "(('fbid', 'campaign', 'content', 'friend_fbid'),)", 'object_name': 'FaceExclusion', 'db_table': "'face_exclusions'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']"}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ClientContent']"}),
            'face_exclusion_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {}),
            'friend_fbid': ('django.db.models.fields.BigIntegerField', [], {}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'targetshare.facesstyle': {
            'Meta': {'object_name': 'FacesStyle', 'db_table': "'faces_styles'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'faces_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        'targetshare.facesstylefiles': {
            'Meta': {'object_name': 'FacesStyleFiles', 'db_table': "'faces_style_files'"},
            'css_file': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.FacesStyle']", 'null': 'True', 'blank': 'True'}),
            'faces_style_file_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'html_template': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.facesstylemeta': {
            'Meta': {'object_name': 'FacesStyleMeta', 'db_table': "'faces_style_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.FacesStyle']", 'null': 'True'}),
            'faces_style_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        'targetshare.fbobject': {
            'Meta': {'object_name': 'FBObject', 'db_table': "'fb_objects'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'fb_object_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        'targetshare.fbobjectattribute': {
            'Meta': {'object_name': 'FBObjectAttribute', 'db_table': "'fb_object_attributes'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.FBObject']", 'null': 'True', 'blank': 'True'}),
            'fb_object_attributes_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msg1_post': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'msg1_pre': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'msg2_post': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'msg2_pre': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'og_action': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'og_description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'og_image': ('django.db.models.fields.CharField', [], {'max_length': '2096', 'blank': 'True'}),
            'og_title': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'og_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'sharing_prompt': ('django.db.models.fields.CharField', [], {'max_length': '2096', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'url_slug': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        },
        'targetshare.fbobjectmeta': {
            'Meta': {'object_name': 'FBObjectMeta', 'db_table': "'fb_object_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.FBObject']", 'null': 'True'}),
            'fb_object_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        'targetshare.filter': {
            'Meta': {'object_name': 'Filter', 'db_table': "'filters'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Client']", 'null': 'True', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'filter_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        'targetshare.filterfeature': {
            'Meta': {'object_name': 'FilterFeature', 'db_table': "'filter_features'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'feature': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Filter']", 'null': 'True'}),
            'filter_feature_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'operator': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'value_type': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'})
        },
        'targetshare.filtermeta': {
            'Meta': {'object_name': 'FilterMeta', 'db_table': "'filter_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'filter_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        'targetshare.mixmodel': {
            'Meta': {'object_name': 'MixModel', 'db_table': "'mix_models'"},
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mix_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'})
        },
        'targetshare.mixmodeldefinition': {
            'Meta': {'object_name': 'MixModelDefinition', 'db_table': "'mix_model_definitions'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.MixModel']", 'null': 'True', 'blank': 'True'}),
            'mix_model_definition_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model_definition': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.mixmodelmeta': {
            'Meta': {'object_name': 'MixModelMeta', 'db_table': "'mix_model_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mix_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.MixModel']", 'null': 'True', 'blank': 'True'}),
            'mix_model_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        'targetshare.propensitymodel': {
            'Meta': {'object_name': 'PropensityModel', 'db_table': "'propensity_models'"},
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'proximity_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'targetshare.propensitymodeldefinition': {
            'Meta': {'object_name': 'PropensityModelDefinition', 'db_table': "'propensity_model_definitions'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'model_definition': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.PropensityModel']", 'null': 'True', 'blank': 'True'}),
            'propensity_model_definition_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'propensity_model_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.propensitymodelmeta': {
            'Meta': {'object_name': 'PropensityModelMeta', 'db_table': "'propensity_model_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'propensity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.PropensityModel']", 'null': 'True'}),
            'propensity_model_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'})
        },
        'targetshare.proximitymodel': {
            'Meta': {'object_name': 'ProximityModel', 'db_table': "'proximity_models'"},
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'proximity_model_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'targetshare.proximitymodeldefinition': {
            'Meta': {'object_name': 'ProximityModelDefinition', 'db_table': "'proximity_model_definitions'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'model_definition': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ProximityModel']", 'null': 'True'}),
            'proximity_model_definition_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.proximitymodelmeta': {
            'Meta': {'object_name': 'ProximityModelMeta', 'db_table': "'proximity_model_meta'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'proximity_model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ProximityModel']", 'null': 'True', 'blank': 'True'}),
            'proximity_model_meta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'})
        },
        'targetshare.sharemessage': {
            'Meta': {'object_name': 'ShareMessage', 'db_table': "'share_messages'"},
            'activity_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ClientContent']", 'null': 'True', 'blank': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'targetshare.userclient': {
            'Meta': {'unique_together': "(('fbid', 'client'),)", 'object_name': 'UserClient', 'db_table': "'user_clients'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {}),
            'user_client_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['targetshare']
