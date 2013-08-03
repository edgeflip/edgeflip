from django.db import models


class Client(models.Model):

    client_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    fb_app_name = models.CharField(max_length=256)
    fb_app_id = models.CharField(max_length=256)
    domain = models.CharField(max_length=256)
    subdomain = models.CharField(max_length=256)
    create_dt = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'clients'
