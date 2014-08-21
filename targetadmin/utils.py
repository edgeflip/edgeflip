import functools
import urllib

from django.conf import settings
from django.contrib.auth import decorators
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator

import chapo.utils

from targetshare import models, utils


FB_OAUTH_URL = 'https://www.facebook.com/dialog/oauth'

INCOMING_SECURE = settings.ENV != 'development'


def superuser_required(view):
    def check_superuser(user):
        if user.is_superuser:
            return True
        raise PermissionDenied
    return decorators.user_passes_test(check_superuser)(view)


# We could remove the internal decorator. I could see it being useful for
# superuser only views, but we don't really have any of these now.
def internal(view):
    is_superuser = superuser_required(view)
    logged_in_superuser = decorators.login_required(is_superuser, login_url='targetadmin:login')
    return logged_in_superuser


def auth_client_required(view):
    @functools.wraps(view)
    @decorators.login_required(login_url='targetadmin:login')
    def verify_client_auth_relation(request, *args, **kwargs):
        pk = kwargs.get('client_pk')
        if (request.user.is_superuser or
                models.Client.objects.filter(
                    pk=pk,
                    auth_groups__user=request.user,
                ).exists()):
            return view(request, *args, **kwargs)
        else:
            return HttpResponseForbidden(
                'You do not have access to this area.'
            )

    if isinstance(view, type):
        view.dispatch = method_decorator(auth_client_required)(view.dispatch)
        return view
    else:
        return verify_client_auth_relation


def fb_oauth_url(client, redirect_uri):
    return FB_OAUTH_URL + '?' + urllib.urlencode([
        ('client_id', client.fb_app_id),
        ('scope', settings.FB_PERMS),
        ('redirect_uri', redirect_uri),
    ])


def build_sharing_urls(incoming_host, campaign, content, incoming_secure=INCOMING_SECURE):
    client = campaign.client
    slug = utils.encodeDES('{}/{}'.format(campaign.pk, content.pk))
    incoming_url = utils.incoming_redirect(incoming_secure, incoming_host, campaign.pk, content.pk)
    oauth_url = fb_oauth_url(client, incoming_url)
    shortened_url = chapo.utils.shorten(oauth_url, prefix=client.codename, campaign=campaign)
    return {
        'slug': slug,
        'incoming_url': incoming_url,
        'fb_oauth_url': oauth_url,
        'initial_url': shortened_url,
    }
