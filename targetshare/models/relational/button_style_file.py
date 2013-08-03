from django.db import models


class ButtonStyleFile(models.Model):

    button_style_file_id = models.AutoField(primary_key=True)
    button_style = models.ForeignKey('ButtonStyle')
    html_template = models.CharField(max_length=256, null=True)
    css_file = models.CharField(max_length=256, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'button_style_files'
