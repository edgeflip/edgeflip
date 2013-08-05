from django.db import models


class Client(models.Model):

    client_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256, unique=True, blank=True)
    fb_app_name = models.CharField(max_length=256, blank=True)
    fb_app_id = models.CharField(max_length=256, blank=True)
    domain = models.CharField(max_length=256, blank=True)
    subdomain = models.CharField(max_length=256, blank=True)
    create_dt = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'clients'
