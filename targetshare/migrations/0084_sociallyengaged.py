# -*- coding: utf-8 -*-
from south.v2 import DataMigration


class Migration(DataMigration):

    def forwards(self, orm):
        """Add Socially Engaged Facebook app and its default required permissions."""
        (fb_app, _created) = orm.FBApp.objects.get_or_create(
            appid=555738104565910,
            name='sociallyengaged',
            defaults={
                'secret': '0d37664e237194e1bf261e77b0243e7f',
                'api': '2.3',
            }
        )

        permissions = [
            orm.FBPermission.objects.get_or_create(code=code)[0]
            for code in (
                'public_profile',
                'user_friends',
                'email',
                'user_birthday',
                'user_location',
                'user_posts',
                'user_likes',
            )
        ]

        fb_app.permissions = permissions

    def backwards(self, orm):
        orm.FBApp.objects.filter(name='sociallyengaged').delete()

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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
            'visit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': "orm['targetshare.Visit']"})
        },
        'targetshare.buttonstyle': {
            'Meta': {'ordering': "('-create_dt',)", 'object_name': 'ButtonStyle', 'db_table': "'button_styles'"},
            'button_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'buttonstyles'", 'null': 'True', 'to': "orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        'targetshare.buttonstylefile': {
            'Meta': {'object_name': 'ButtonStyleFile', 'db_table': "'button_style_files'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'buttonstylefiles'", 'null': 'True', 'to': "orm['targetshare.ButtonStyle']"}),
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
            'client': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'campaigns'", 'null': 'True', 'to': "orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        'targetshare.campaignbuttonstyle': {
            'Meta': {'object_name': 'CampaignButtonStyle', 'db_table': "'campaign_button_styles'"},
            'button_style': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ButtonStyle']", 'null': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'campaignbuttonstyles'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'campaign_button_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignchoiceset': {
            'Meta': {'object_name': 'CampaignChoiceSet', 'db_table': "'campaign_choice_sets'"},
            'allow_generic': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'campaignchoicesets'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'campaign_choice_set_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'campaignchoicesets'", 'null': 'True', 'to': "orm['targetshare.ChoiceSet']"}),
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
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'campaignfacesstyles'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'campaign_faces_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.FacesStyle']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignfbobject': {
            'Meta': {'unique_together': "(('campaign', 'source_url'),)", 'object_name': 'CampaignFBObject', 'db_table': "'campaign_fb_objects'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'campaignfbobjects'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'campaign_fb_object_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'campaignfbobjects'", 'null': 'True', 'to': "orm['targetshare.FBObject']"}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Filter']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'sourced': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaigngenericfbobjects': {
            'Meta': {'object_name': 'CampaignGenericFBObjects', 'db_table': "'campaign_generic_fb_objects'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'campaigngenericfbobjects'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'campaign_generic_fb_object_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fb_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.FBObject']", 'null': 'True', 'blank': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '9', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.campaignglobalfilter': {
            'Meta': {'object_name': 'CampaignGlobalFilter', 'db_table': "'campaign_global_filters'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'campaignglobalfilters'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'campaign_global_filter_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'campaignglobalfilters'", 'null': 'True', 'to': "orm['targetshare.Filter']"}),
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
        'targetshare.campaignpagestyleset': {
            'Meta': {'object_name': 'CampaignPageStyleSet', 'db_table': "'campaign_page_style_sets'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'campaignpagestylesets'", 'to': "orm['targetshare.Campaign']"}),
            'campaign_page_style_set_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'page_style_set': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['targetshare.PageStyleSet']", 'unique': 'True'}),
            'rand_cdf': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '9'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
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
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'campaignproperties'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'campaign_property_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'client_content': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'campaignproperties'", 'null': 'True', 'db_column': "'content_id'", 'to': "orm['targetshare.ClientContent']"}),
            'client_error_url': ('django.db.models.fields.CharField', [], {'max_length': '2096'}),
            'client_faces_url': ('django.db.models.fields.CharField', [], {'max_length': '2096'}),
            'client_thanks_url': ('django.db.models.fields.CharField', [], {'max_length': '2096'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'fallback_campaign': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fallbackcampaign_properties'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'fallback_content': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fallbackcampaign_properties'", 'null': 'True', 'to': "orm['targetshare.ClientContent']"}),
            'fallback_is_cascading': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'inactive_url': ('django.db.models.fields.CharField', [], {'max_length': '2096', 'blank': 'True'}),
            'min_friends': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'num_faces': ('django.db.models.fields.PositiveIntegerField', [], {'default': '10'}),
            'root_campaign': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rootcampaign_properties'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "u'draft'", 'max_length': '32'})
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
        'targetshare.campaignrankingkey': {
            'Meta': {'ordering': "('start_dt',)", 'object_name': 'CampaignRankingKey', 'db_table': "'campaign_ranking_keys'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'campaignrankingkeys'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'campaign_ranking_key_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'ranking_key': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'campaignrankingkeys'", 'null': 'True', 'to': "orm['targetshare.RankingKey']"}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'targetshare.choiceset': {
            'Meta': {'ordering': "('-create_dt',)", 'object_name': 'ChoiceSet', 'db_table': "'choice_sets'"},
            'choice_set_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'choicesets'", 'null': 'True', 'to': "orm['targetshare.Client']"}),
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
            'choice_set': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'choicesetfilters'", 'null': 'True', 'to': "orm['targetshare.ChoiceSet']"}),
            'choice_set_filter_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'choicesetfilters'", 'null': 'True', 'to': "orm['targetshare.Filter']"}),
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
            'auth_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'campaign_inactive_url': ('django.db.models.fields.CharField', [], {'max_length': '2096'}),
            'client_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'codename': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'fb_app': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'clients'", 'to': "orm['targetshare.FBApp']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'source_parameter': ('django.db.models.fields.CharField', [], {'default': "'rs'", 'max_length': '15', 'blank': 'True'}),
            'subdomain': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        'targetshare.clientcontent': {
            'Meta': {'ordering': "('-create_dt',)", 'object_name': 'ClientContent', 'db_table': "'client_content'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'clientcontent'", 'null': 'True', 'to': "orm['targetshare.Client']"}),
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
            'client': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'clientdefaults'", 'null': 'True', 'to': "orm['targetshare.Client']"}),
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
            'Meta': {'ordering': "('event_datetime',)", 'object_name': 'Event', 'db_table': "'events'"},
            'activity_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True'}),
            'client_content': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ClientContent']", 'null': 'True', 'db_column': "'content_id'"}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '1028', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'event_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_column': "'type'"}),
            'friend_fbid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'visit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': "orm['targetshare.Visit']"})
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
            'faces_style': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'facesstylefiles'", 'null': 'True', 'to': "orm['targetshare.FacesStyle']"}),
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
        'targetshare.fbapp': {
            'Meta': {'ordering': "('name',)", 'object_name': 'FBApp', 'db_table': "'fb_apps'"},
            'api': ('django.db.models.fields.DecimalField', [], {'default': "'2.2'", 'max_digits': '3', 'decimal_places': '1'}),
            'appid': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['targetshare.FBPermission']", 'symmetrical': 'False', 'blank': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'targetshare.fbobject': {
            'Meta': {'ordering': "('-create_dt',)", 'object_name': 'FBObject', 'db_table': "'fb_objects'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'fbobjects'", 'null': 'True', 'to': "orm['targetshare.Client']"}),
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
            'org_name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'sharing_button': ('django.db.models.fields.CharField', [], {'default': "'Show Your Support'", 'max_length': '25'}),
            'sharing_prompt': ('django.db.models.fields.CharField', [], {'max_length': '2096', 'blank': 'True'}),
            'sharing_sub_header': ('django.db.models.fields.CharField', [], {'max_length': '2096', 'blank': 'True'}),
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
        'targetshare.fbpermission': {
            'Meta': {'ordering': "('code',)", 'object_name': 'FBPermission', 'db_table': "'fb_permissions'"},
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '64', 'primary_key': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'targetshare.filter': {
            'Meta': {'ordering': "('-create_dt',)", 'object_name': 'Filter', 'db_table': "'filters'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'filters'", 'null': 'True', 'to': "orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'filter_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        'targetshare.filterfeature': {
            'Meta': {'ordering': "('feature_type__sort_order',)", 'object_name': 'FilterFeature', 'db_table': "'filter_features'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'feature': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'feature_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.FilterFeatureType']"}),
            'filter': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'filterfeatures'", 'null': 'True', 'to': "orm['targetshare.Filter']"}),
            'filter_feature_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'operator': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'value_type': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'})
        },
        'targetshare.filterfeaturetype': {
            'Meta': {'ordering': "('sort_order',)", 'object_name': 'FilterFeatureType', 'db_table': "'filter_feature_types'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'px_rank': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '0'})
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
        'targetshare.notification': {
            'Meta': {'object_name': 'Notification', 'db_table': "'notifications'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']"}),
            'client_content': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ClientContent']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'notification_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'targetshare.notificationassignment': {
            'Meta': {'object_name': 'NotificationAssignment', 'db_table': "'notification_assignments'"},
            'assign_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True', 'blank': 'True'}),
            'chosen_from_rows': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'chosen_from_table': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ClientContent']", 'null': 'True', 'blank': 'True'}),
            'feature_row': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'feature_type': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'notification_assignment_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': "orm['targetshare.NotificationUser']"}),
            'random_assign': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        'targetshare.notificationevent': {
            'Meta': {'object_name': 'NotificationEvent', 'db_table': "'notification_events'"},
            'activity_id': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True'}),
            'client_content': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.ClientContent']", 'null': 'True', 'db_column': "'content_id'"}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '1028', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'event_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_column': "'type'"}),
            'friend_fbid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notification_event_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': "orm['targetshare.NotificationUser']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'targetshare.notificationuser': {
            'Meta': {'object_name': 'NotificationUser', 'db_table': "'notification_users'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {}),
            'notification': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notificationusers'", 'to': "orm['targetshare.Notification']"}),
            'notification_user_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'})
        },
        'targetshare.page': {
            'Meta': {'object_name': 'Page', 'db_table': "'pages'"},
            'code': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'page_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'targetshare.pagestyle': {
            'Meta': {'unique_together': "(('name', 'client'),)", 'object_name': 'PageStyle', 'db_table': "'page_styles'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pagestyles'", 'null': 'True', 'to': "orm['targetshare.Client']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pagestyles'", 'to': "orm['targetshare.Page']"}),
            'page_style_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'starred': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'targetshare.pagestyleset': {
            'Meta': {'object_name': 'PageStyleSet', 'db_table': "'page_style_sets'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'page_style_set_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page_styles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'pagestylesets'", 'symmetrical': 'False', 'to': "orm['targetshare.PageStyle']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
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
        'targetshare.rankingfeaturetype': {
            'Meta': {'object_name': 'RankingFeatureType', 'db_table': "'ranking_feature_types'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'targetshare.rankingkey': {
            'Meta': {'ordering': "('-create_dt',)", 'object_name': 'RankingKey', 'db_table': "'ranking_keys'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rankingkeys'", 'null': 'True', 'to': "orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delete_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'ranking_key_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'refinement_weight': ('django.db.models.fields.FloatField', [], {'default': '0.5', 'blank': 'True'})
        },
        'targetshare.rankingkeyfeature': {
            'Meta': {'ordering': "('ordinal_position',)", 'unique_together': "(('ranking_key', 'ordinal_position'),)", 'object_name': 'RankingKeyFeature', 'db_table': "'ranking_key_features'"},
            'end_dt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'feature': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'feature_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.RankingFeatureType']"}),
            'global_maximum': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'ordinal_position': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ranking_key': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rankingkeyfeatures'", 'null': 'True', 'to': "orm['targetshare.RankingKey']"}),
            'ranking_key_feature_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reverse': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
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
            'client': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userclients'", 'to': "orm['targetshare.Client']"}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {}),
            'user_client_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'targetshare.visit': {
            'Meta': {'unique_together': "(('session_id', 'app_id'),)", 'object_name': 'Visit', 'db_table': "'visits'"},
            'app_id': ('django.db.models.fields.BigIntegerField', [], {'db_column': "'appid'"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'ip': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39'}),
            'referer': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1028', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'db_index': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user_agent': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1028', 'blank': 'True'}),
            'visit_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'visitor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'visits'", 'to': "orm['targetshare.Visitor']"})
        },
        'targetshare.visitor': {
            'Meta': {'object_name': 'Visitor', 'db_table': "'visitors'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '40'}),
            'visitor_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['targetshare']
    symmetrical = True
