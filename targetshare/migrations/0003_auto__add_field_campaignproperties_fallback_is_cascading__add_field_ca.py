# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'CampaignProperties.fallback_is_cascading'
        db.add_column('campaign_properties', 'fallback_is_cascading',
                      self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'CampaignProperties.min_friends'
        db.add_column('campaign_properties', 'min_friends',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

        # Changing field 'Event.campaign'
        db.alter_column('events', 'campaign_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True))

    def backwards(self, orm):
        # Deleting field 'CampaignProperties.fallback_is_cascading'
        db.delete_column('campaign_properties', 'fallback_is_cascading')

        # Deleting field 'CampaignProperties.min_friends'
        db.delete_column('campaign_properties', 'min_friends')

        # User chose to not deal with backwards NULL issues for 'Event.campaign'
        raise RuntimeError("Cannot reverse this migration. 'Event.campaign' and its values cannot be restored.")

    models = {
        u'targetshare.assignment': {
            'Meta': {'object_name': 'Assignment', 'db_table': "'assignments'"},
            'assign_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'assignment_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'Meta': {'object_name': 'CampaignGlobalFilter', 'db_table': "'campaign_global_filters'"},
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
            'fallback_is_cascading': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'min_friends': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
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
            'edge_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.Campaign']", 'null': 'True'}),
            'client_content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['targetshare.ClientContent']", 'null': 'True', 'db_column': "'client_id'"}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'event_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'face_exclusion_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'user_client_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['targetshare']
