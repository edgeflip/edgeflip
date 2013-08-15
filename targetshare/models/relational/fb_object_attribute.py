from django.db import models


class FBObjectAttribute(models.Model):

    fb_object_attributes_id = models.AutoField(primary_key=True)
    fb_object = models.ForeignKey('FBObject', null=True, blank=True)
    og_action = models.CharField(max_length=64, blank=True)
    og_type = models.CharField(max_length=64, blank=True)
    og_title = models.CharField(max_length=128, blank=True)
    og_image = models.CharField(max_length=2096, blank=True)
    og_description = models.CharField(max_length=1024, blank=True)
    page_title = models.CharField(max_length=256, blank=True)
    sharing_prompt = models.CharField(max_length=2096, blank=True)
    msg1_pre = models.CharField(max_length=1024, blank=True)
    msg1_post = models.CharField(max_length=1024, blank=True)
    msg2_pre = models.CharField(max_length=1024, blank=True)
    msg2_post = models.CharField(max_length=1024, blank=True)
    url_slug = models.CharField(max_length=64, blank=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'fb_object_attributes'
