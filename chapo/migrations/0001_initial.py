# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ShortenedUrl'
        db.create_table('shortened_urls', (
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['targetshare.Campaign'], null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('event_type', self.gf('django.db.models.fields.SlugField')(default='generic_redirect', max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=2048)),
        ))
        db.send_create_signal(u'chapo', ['ShortenedUrl'])

    def backwards(self, orm):
        # Deleting model 'ShortenedUrl'
        db.delete_table('shortened_urls')

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
        u'chapo.shortenedurl': {
            'Meta': {'object_name': 'ShortenedUrl', 'db_table': "'shortened_urls'"},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['targetshare.Campaign']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'event_type': ('django.db.models.fields.SlugField', [], {'default': "'generic_redirect'", 'max_length': '50'}),
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
            '_fb_app_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_column': "'fb_app_id'", 'blank': 'True'}),
            '_fb_app_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_column': "'fb_app_name'", 'blank': 'True'}),
            'auth_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'client_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'codename': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'blank': 'True'}),
            'create_dt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'source_parameter': ('django.db.models.fields.CharField', [], {'default': "'rs'", 'max_length': '15', 'blank': 'True'}),
            'subdomain': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        }
    }

    complete_apps = ['chapo']
