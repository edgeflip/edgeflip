from django.db import models
from django.template import TemplateDoesNotExist
from django.template.loader import find_template


class Client(models.Model):

    client_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, blank=True)
    fb_app_name = models.CharField(max_length=256, blank=True)
    fb_app_id = models.CharField(max_length=256, blank=True)
    domain = models.CharField(max_length=256, blank=True)
    subdomain = models.CharField(max_length=256, blank=True)
    create_dt = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s' % self.name

    def locate_template(self, template_name):
        ''' Attempts to locate a given template name in the clients template
        path. If it doesn't find one, returns the default template
        '''
        try:
            template = find_template('targetshare/clients/%s/%s' % (
                self.subdomain,
                template_name
            ))[0]
        except TemplateDoesNotExist:
            template = 'targetshare/%s' % template_name

        return template

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'clients'
