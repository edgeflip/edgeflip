# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EngagedUser'
        db.create_table('engaged_users', (
            ('fbid', self.gf('django.db.models.fields.BigIntegerField')(primary_key=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('birthday', self.gf('django.db.models.fields.DateField')(null=True, db_index=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=256, db_index=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('score', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'gimmick', ['EngagedUser'])

    def backwards(self, orm):
        # Deleting model 'EngagedUser'
        db.delete_table('engaged_users')

    models = {
        u'gimmick.engageduser': {
            'Meta': {'object_name': 'EngagedUser', 'db_table': "'engaged_users'"},
            'birthday': ('django.db.models.fields.DateField', [], {'null': 'True', 'db_index': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fbid': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'score': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['gimmick']
