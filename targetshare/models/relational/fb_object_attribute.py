from django.db import models


class FBObjectAttribute(models.Model):

    fb_object_attributes_id = models.AutoField(primary_key=True)
    fb_object = models.ForeignKey('FBObject')
    og_action = models.CharField(max_length=64, null=True)
    og_type = models.CharField(max_length=64, null=True)
    og_title = models.CharField(max_length=128, null=True)
    og_image = models.CharField(max_length=2096, null=True)
    og_description = models.CharField(max_length=1024, null=True)
    page_title = models.CharField(max_length=256, null=True)
    sharing_prompt = models.CharField(max_length=2096, null=True)
    msg1_pre = models.CharField(max_length=1024, null=True)
    msg1_post = models.CharField(max_length=1024, null=True)
    msg2_pre = models.CharField(max_length=1024, null=True)
    msg2_post = models.CharField(max_length=1024, null=True)
    url_slug = models.CharField(max_length=64, null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'fb_object_attributes'
