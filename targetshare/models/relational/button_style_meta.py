from django.db import models


class ButtonStyleMeta(models.Model):

    button_style_meta_id = models.AutoField(primary_key=True)
    button_style = models.ForeignKey('ButtonStyle', null=True)
    name = models.CharField(max_length=256)
    value = models.TextField(blank=True, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'button_style_meta'
