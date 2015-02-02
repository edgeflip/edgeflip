import urllib

from django.conf import settings
from django.core.urlresolvers import reverse

import chapo.utils
from core.utils import encryptedslug


FB_OAUTH_URL = 'https://www.facebook.com/dialog/oauth'


def fb_oauth_url(fb_app, redirect_uri):
    app_permissions = fb_app.permissions.values_list('code', flat=True)
    return FB_OAUTH_URL + '?' + urllib.urlencode([
        ('client_id', fb_app.appid),
        ('scope', ','.join(app_permissions.iterator())),
        ('redirect_uri', redirect_uri),
    ])


def incoming_redirect(is_secure, host, campaign=None, content=None, slug=None):
    if slug is None:
        if campaign is None or content is None:
            raise TypeError("Either slug or campaign and content required")
        slug = encryptedslug.make_slug(campaign, content)
    path = reverse('incoming-encoded', args=(slug,))
    protocol = 'https://' if is_secure else 'http://'
    return protocol + host + path


def client_faces_url(campaign, content):
    slug = encryptedslug.make_slug(campaign, content)
    if settings.ENV == 'development':
        endpoint = 'http://local.edgeflip.com:8080'
        path = reverse('frame-faces-encoded', args=(slug,))
    else:
        endpoint = 'https://apps.facebook.com'
        path = '/{}/{}/'.format(campaign.client.fb_app.name, slug)
    return endpoint + path


def build_urls(incoming_host, campaign, content, incoming_secure=settings.INCOMING_REQUEST_SECURE):
    client = campaign.client
    slug = encryptedslug.make_slug(campaign, content)
    incoming_url = incoming_redirect(incoming_secure, incoming_host, slug=slug)
    oauth_url = fb_oauth_url(client.fb_app, incoming_url)
    shortened_url = chapo.utils.shorten(oauth_url, prefix=client.codename, campaign=campaign)
    return {
        'slug': slug,
        'incoming_url': incoming_url,
        'fb_oauth_url': oauth_url,
        'initial_url': shortened_url,
    }


def initial_url(*args, **kws):
    urls = build_urls(*args, **kws)
    return urls['initial_url']
