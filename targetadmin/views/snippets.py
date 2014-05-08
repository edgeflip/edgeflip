import functools
import urllib

from django.conf import settings
from django.shortcuts import get_object_or_404, render

from targetshare import utils
from targetshare.models import relational
from targetshare.views.utils import JsonHttpResponse

from targetadmin import forms
from targetadmin.utils import auth_client_required


INCOMING_SECURE = settings.ENV != 'development'

incoming_redirect = functools.partial(utils.incoming_redirect, INCOMING_SECURE)


FB_OAUTH_URL = 'https://www.facebook.com/dialog/oauth'


def mk_fb_oauth_url(client, redirect_uri):
    return FB_OAUTH_URL + '?' + urllib.urlencode([
        ('client_id', client.fb_app_id),
        ('scope', settings.FB_PERMS),
        ('redirect_uri', redirect_uri),
    ])


@auth_client_required
def snippets(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)

    try:
        first_campaign = client.campaigns.get(pk=request.GET.get('campaign_pk'))
    except relational.Campaign.DoesNotExist:
        try:
            first_campaign = client.campaigns.exclude(rootcampaign_properties=None)[0]
        except IndexError:
            first_campaign = None

    try:
        first_content = client.clientcontent.get(pk=request.GET.get('content_pk'))
    except relational.ClientContent.DoesNotExist:
        try:
            first_content = client.clientcontent.all()[0]
        except IndexError:
            first_content = None

    if first_campaign and first_content:
        first_faces_url = incoming_redirect(request.get_host(), first_campaign.pk, first_content.pk)

        first_slug = utils.encodeDES('{}/{}'.format(
            first_campaign.pk, first_content.pk))

        snippet_form = forms.SnippetForm(client=client, initial={
            'campaign': first_campaign,
            'content': first_content
        })
    else:
        first_slug = first_faces_url = None
        snippet_form = forms.SnippetForm(client=client)

    return render(request, 'targetadmin/snippets.html', {
        'client': client,
        'first_campaign': first_campaign,
        'first_content': first_content,
        'first_slug': first_slug,
        'oauth_url': first_faces_url and mk_fb_oauth_url(client, first_faces_url),
        'snippet_form': snippet_form,
    })


@auth_client_required
def snippet_update(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    snippet_form = forms.SnippetForm(client=client, data=request.GET)

    if snippet_form.is_valid():
        campaign = snippet_form.cleaned_data['campaign']
        content = snippet_form.cleaned_data['content']
        faces_url = incoming_redirect(request.get_host(), campaign.pk, content.pk)
        slug = utils.encodeDES('{}/{}'.format(campaign.pk, content.pk))
    else:
        slug = faces_url = None

    return JsonHttpResponse({
        'slug': slug,
        'oauth_url': faces_url and mk_fb_oauth_url(client, faces_url),
    })
