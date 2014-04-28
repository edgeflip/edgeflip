from django.db import models

from targetshare.models.relational import manager


class BaseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = manager.Manager()

    class Meta(object):
        abstract = True
        app_label = 'targetshare'

    def __str__(self):
        return unicode(self).encode('utf8')
