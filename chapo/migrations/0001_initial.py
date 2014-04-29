# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ShortenedUrl'
        db.create_table('shortened_urls', (
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=2048)),
        ))
        db.send_create_signal(u'chapo', ['ShortenedUrl'])

    def backwards(self, orm):
        # Deleting model 'ShortenedUrl'
        db.delete_table('shortened_urls')

    models = {
        u'chapo.shortenedurl': {
            'Meta': {'object_name': 'ShortenedUrl', 'db_table': "'shortened_urls'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'default': "'2kSiPbxMShClQRTX6R2RwA'", 'max_length': '50', 'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '2048'})
        }
    }

    complete_apps = ['chapo']
