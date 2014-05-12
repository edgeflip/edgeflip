import urllib

import chapo.utils
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from targetshare import utils
from targetshare.models import relational
from targetshare.views.utils import JsonHttpResponse

from targetadmin import forms
from targetadmin.utils import auth_client_required


FB_OAUTH_URL = 'https://www.facebook.com/dialog/oauth'


def fb_oauth_url(client, redirect_uri):
    return FB_OAUTH_URL + '?' + urllib.urlencode([
        ('client_id', client.fb_app_id),
        ('scope', settings.FB_PERMS),
        ('redirect_uri', redirect_uri),
    ])


INCOMING_SECURE = settings.ENV != 'development'


def make_context(incoming_host, campaign, content):
    client = campaign.client
    slug = utils.encodeDES('{}/{}'.format(campaign.pk, content.pk))
    incoming_url = utils.incoming_redirect(INCOMING_SECURE, incoming_host, campaign.pk, content.pk)
    oauth_url = fb_oauth_url(client, incoming_url)
    shortened_url = chapo.utils.shorten(oauth_url, prefix=client.codename, campaign=campaign)
    return {
        'slug': slug,
        'oauth_url': oauth_url,
        'shortened_url': shortened_url,
    }


@auth_client_required
@require_GET
def snippets(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)

    try:
        first_campaign = client.campaigns.get(pk=request.GET.get('campaign_pk', ''))
    except (relational.Campaign.DoesNotExist, ValueError):
        try:
            first_campaign = client.campaigns.exclude(rootcampaign_properties=None)[0]
        except IndexError:
            first_campaign = None

    try:
        first_content = client.clientcontent.get(pk=request.GET.get('content_pk', ''))
    except (relational.ClientContent.DoesNotExist, ValueError):
        try:
            first_content = client.clientcontent.all()[0]
        except IndexError:
            first_content = None

    if first_campaign and first_content:
        context = {
            'snippet_form': forms.SnippetForm(client=client, initial={
                'campaign': first_campaign,
                'content': first_content,
            }),
        }
        context.update(make_context(request.get_host(), first_campaign, first_content))
    else:
        context = {'snippet_form': forms.SnippetForm(client=client)}

    context.update(
        client=client,
        campaign=first_campaign,
        content=first_content,
    )
    return render(request, 'targetadmin/snippets.html', context)


@auth_client_required
@require_GET
def snippet_update(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    snippet_form = forms.SnippetForm(client=client, data=request.GET)

    if snippet_form.is_valid():
        campaign = snippet_form.cleaned_data['campaign']
        content = snippet_form.cleaned_data['content']
        return JsonHttpResponse(make_context(request.get_host(), campaign, content))

    return JsonHttpResponse(snippet_form.errors, status=400)
