import string

from django.db import models
from django.utils.crypto import get_random_string

from . import manager


class Visitor(models.Model):

    visitor_id = models.AutoField(primary_key=True)
    uuid = models.CharField(unique=True, max_length=40)
    fbid = models.BigIntegerField(unique=True, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = manager.Manager()

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'visitors'

    @classmethod
    def get_new_uuid(cls):
        """Return a UUID that isn't being used."""
        while True:
            uuid = get_random_string(40, string.ascii_uppercase + string.digits)
            if not cls._default_manager.filter(uuid=uuid).exists():
                return uuid

    def save(self, *args, **kws):
        # Ensure uuid is set:
        if not self.uuid:
            self.uuid = self.get_new_uuid()
        return super(Visitor, self).save(*args, **kws)

    def __unicode__(self):
        return u"{} [{}]".format(self.uuid, self.fbid or '')
