from django.db import models


class ButtonStyleFile(models.Model):

    button_style_file_id = models.AutoField(primary_key=True)
    button_style = models.ForeignKey('ButtonStyle',
                                     related_name='buttonstylefiles',
                                     null=True, blank=True)
    html_template = models.CharField(max_length=256, blank=True)
    css_file = models.CharField(max_length=256, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'button_style_files'
