from django.db import models

from core.models import manager


class BaseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = manager.Manager()

    class Meta(object):
        abstract = True

    def __str__(self):
        return unicode(self).encode('utf8')
