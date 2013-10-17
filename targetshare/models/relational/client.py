from django.conf import settings
from django.db import models


class Client(models.Model):

    client_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, blank=True)
    codename = models.SlugField(unique=True)
    _fb_app_name = models.CharField(
        'FB App Namespace',
        max_length=256,
        db_column='fb_app_name',
        blank=True
    )
    _fb_app_id = models.CharField(
        'FB App ID',
        max_length=256,
        db_column='fb_app_id',
        blank=True
    )
    domain = models.CharField(max_length=256, blank=True)
    subdomain = models.CharField(max_length=256, blank=True)
    source_parameter = models.CharField(
        "Query string key, if any, with which Edgeflip identifies itself "
        "on links outgoing to client",
        blank=True,
        default='rs',
        max_length=15,
    )
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
