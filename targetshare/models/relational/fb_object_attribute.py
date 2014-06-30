from django.db import models
from django.conf import settings

from . import manager

import uuid
import os

def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('facesloading', filename)

class FBObjectAttribute(models.Model):

    fb_object_attributes_id = models.AutoField(primary_key=True)
    fb_object = models.ForeignKey('FBObject', null=True, blank=True)
    og_action = models.CharField('Action', max_length=64, blank=True)
    og_type = models.CharField('Type', max_length=64, blank=True)
    og_title = models.CharField('Title', max_length=128, blank=True)
    og_image = models.CharField('Image URL', max_length=2096, blank=True)
    og_description = models.CharField('FB Object Description',
                                      max_length=1024, blank=True)
    org_name = models.CharField('Organization Name',
                                max_length=1024, blank=True)
    page_title = models.CharField(max_length=256, blank=True)
    sharing_prompt = models.CharField('Headline', max_length=2096, blank=True)
    sharing_sub_header = models.CharField('Sub-Header', max_length=2096, blank=True)
    sharing_button = models.CharField(max_length=100, blank=True, default="Show Your Support")
    msg1_pre = models.CharField('Message 1 Pre', max_length=1024, blank=True)
    msg1_post = models.CharField('Message 1 Post', max_length=1024, blank=True)
    msg2_pre = models.CharField('Message 2 Pre', max_length=1024, blank=True)
    msg2_post = models.CharField('Message 2 Post', max_length=1024, blank=True)
    url_slug = models.CharField(max_length=64, blank=True)
    loading_image = models.FileField(upload_to=get_file_path)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True, blank=True)

    objects = manager.TransitoryObjectManager.make(
        source_fields=(
            og_action,
            og_type,
            og_title,
            og_image,
            og_description,
            org_name,
            page_title,
            sharing_prompt,
            msg1_pre,
            msg1_post,
            msg2_pre,
            msg2_post,
            url_slug,
            loading_image
        )
    )

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'fb_object_attributes'

