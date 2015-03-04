# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EFApiUser'
        db.create_table('ef_api_users', (
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=30, primary_key=True, db_column='ef_api_user_name')),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'chapo', ['EFApiUser'])

        # Adding model 'EFApp'
        db.create_table('ef_apps', (
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=30, primary_key=True, db_column='ef_app_name')),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'chapo', ['EFApp'])

        # Adding model 'EFApiKey'
        db.create_table('ef_api_keys', (
            ('key', self.gf('django.db.models.fields.SlugField')(max_length=40, primary_key=True, db_column='ef_api_key')),
            ('ef_api_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='efapikeys', db_column='ef_api_user_name', to=orm['chapo.EFApiUser'])),
            ('ef_app', self.gf('django.db.models.fields.related.ForeignKey')(related_name='efapikeys', db_column='ef_app_name', to=orm['chapo.EFApp'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'chapo', ['EFApiKey'])

    def backwards(self, orm):
        # Deleting model 'EFApiUser'
        db.delete_table('ef_api_users')

        # Deleting model 'EFApp'
        db.delete_table('ef_apps')

        # Deleting model 'EFApiKey'
        db.delete_table('ef_api_keys')

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
        u'chapo.efapikey': {
            'Meta': {'object_name': 'EFApiKey', 'db_table': "'ef_api_keys'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'ef_api_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'efapikeys'", 'db_column': "'ef_api_user_name'", 'to': u"orm['chapo.EFApiUser']"}),
            'ef_app': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'efapikeys'", 'db_column': "'ef_app_name'", 'to': u"orm['chapo.EFApp']"}),
            'key': ('django.db.models.fields.SlugField', [], {'max_length': '40', 'primary_key': 'True', 'db_column': "'ef_api_key'"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'chapo.efapiuser': {
            'Meta': {'object_name': 'EFApiUser', 'db_table': "'ef_api_users'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '30', 'primary_key': 'True', 'db_column': "'ef_api_user_name'"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'chapo.efapp': {
            'Meta': {'object_name': 'EFApp', 'db_table': "'ef_apps'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '30', 'primary_key': 'True', 'db_column': "'ef_app_name'"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'chapo.shortenedurl': {
            'Meta': {'object_name': 'ShortenedUrl', 'db_table': "'shortened_urls'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'shortenedurls'", 'null': 'True', 'to': "orm['targetshare.Campaign']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'event_type': ('django.db.models.fields.SlugField', [], {'default': "'generic_redirect'", 'max_length': '50', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '2048'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
        'targetshare.fbpermission': {
            'Meta': {'ordering': "('code',)", 'object_name': 'FBPermission', 'db_table': "'fb_permissions'"},
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '64', 'primary_key': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['chapo']
