from django.conf import settings
from django.db import models
from django.utils import text


class Client(models.Model):

    client_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, blank=True)
    codename = models.SlugField(unique=True, blank=True, editable=False)
    fb_app_id = models.BigIntegerField('FB App ID', null=True, blank=True)
    fb_app_name = models.CharField('FB App Namespace', max_length=256, blank=True)
    fb_app_permissions = models.ManyToManyField('targetshare.FBPermission', blank=True)
    domain = models.CharField(max_length=256, blank=True)
    subdomain = models.CharField(max_length=256, blank=True)
    campaign_inactive_url = models.CharField(
        max_length=2096,
        help_text="Default URL to which to redirect visitors "
                  "once a campaign has been archived.",
    )
    source_parameter = models.CharField(
        blank=True,
        default='rs',
        max_length=15,
        help_text="Query string key, if any, with which Edgeflip identifies itself "
                  "on links outgoing to client",
    )
    auth_groups = models.ManyToManyField('auth.Group', blank=True)
    create_dt = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'clients'

    def __unicode__(self):
        return self.name

    @property
    def hostname(self):
        return u"{client.subdomain}.{client.domain}".format(client=self)

    def save(self, *args, **kws):
        # Ensure domain:
        if bool(self.domain) is not bool(self.subdomain):
            raise ValueError("Cannot populate only domain or only subdomain")
        elif not self.domain:
            self.subdomain = settings.WEB.edgeflip_subdomain
            self.domain = settings.WEB.edgeflip_domain

        # Ensure codename is set:
        if not self.codename:
            self.codename = text.slugify(self.name.decode(settings.DEFAULT_CHARSET))

        return super(Client, self).save(*args, **kws)
