from django.db import models

from .base import BaseModel


class FBPermission(BaseModel):

    code = models.SlugField(max_length=64, primary_key=True)

    def __unicode__(self):
        return self.code

    class Meta(BaseModel.Meta):
        db_table = 'fb_permissions'
        ordering = ('code',)
