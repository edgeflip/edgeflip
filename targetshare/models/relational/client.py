import os

from django.conf import settings
from django.db import models
from django.template import TemplateDoesNotExist
from django.template.loader import find_template


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
        return settings.FACEBOOK.get('appid_override', self._fb_app_id)

    def locate_template(self, template_name):
        ''' Attempts to locate a given template name in the clients template
        path. If it doesn't find one, returns the default template
        '''
        try:
            template = find_template('targetshare/clients/%s/%s' % (
                self.subdomain,
                template_name
            ))[0].name
        except TemplateDoesNotExist:
            template = 'targetshare/%s' % template_name

        return template

    def locate_css(self, css_name):
        ''' Attempts to locate a given css file name in the static path. If
        one is found, it'll be returned, otherwise we kick back the default
        '''
        css_path = os.path.join(
            settings.STATIC_ROOT,
            'css',
            'clients',
            self.subdomain,
            css_name
        )
        if os.path.exists(css_path):
            return '%scss/clients/%s/%s' % (
                settings.STATIC_URL,
                self.subdomain,
                css_name
            )
        else:
            return '%scss/%s' % (
                settings.STATIC_URL,
                css_name
            )

    class Meta(object):
        app_label = 'targetshare'
        db_table = 'clients'
