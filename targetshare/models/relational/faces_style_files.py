from django.db import models


class FacesStyleFiles(models.Model):

    faces_style_file_id = models.AutoField(primary_key=True)
    faces_style = models.ForeignKey('FacesStyle', null=True, blank=True)
    html_template = models.CharField(max_length=128, blank=True)
    css_file = models.CharField(max_length=128, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'faces_style_files'
