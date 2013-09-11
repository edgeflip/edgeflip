from django.conf import settings
from django.db import models


class Client(models.Model):

    client_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, blank=True)
    _fb_app_name = models.CharField(
        max_length=256,
        db_column='fb_app_name',
        blank=True
    )
    _fb_app_id = models.CharField(
        max_length=256,
        db_column='fb_app_id',
        blank=True
    )
    domain = models.CharField(max_length=256, blank=True)
    subdomain = models.CharField(max_length=256, blank=True)
    create_dt = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s' % self.name

    # FIXME: Kill me once the client admin tool is more proper
    @property
    def fb_app_name(self):
        return settings.FACEBOOK.get('appname_override', self._fb_app_name)

    # FIXME: Kill me once the client admin tool is more proper
    @property
    def fb_app_id(self):
        return int(settings.FACEBOOK.get('appid_override', self._fb_app_id))

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'clients'
