from django.shortcuts import get_object_or_404, render

from targetadmin.utils import auth_client_required
from targetshare.models import relational
from targetshare.utils import encodeDES, incoming_redirect
from targetshare.views import utils


@auth_client_required
def snippets(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    try:
        first_campaign = client.campaigns.get(pk=request.GET.get('campaign_pk'))
    except relational.Campaign.DoesNotExist:
        try:
            first_campaign = client.campaigns.all()[0]
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
        first_faces_url = incoming_redirect(
            request.is_secure(), request.get_host(),
            first_campaign.pk, first_content.pk)
    return render(request, 'targetadmin/snippets.html', {
        'client': client,
        'first_campaign': first_campaign,
        'first_content': first_content,
        'first_faces_url': first_faces_url,
    })


@auth_client_required
def snippet_update(request, client_pk, campaign_pk, content_pk):
    get_object_or_404(relational.Client, pk=client_pk)
    campaign = get_object_or_404(relational.Campaign, pk=campaign_pk)
    content = get_object_or_404(relational.ClientContent, pk=content_pk)
    faces_url = incoming_redirect(
        request.is_secure(), request.get_host(), campaign.pk, content.pk)
    return utils.JsonHttpResponse({
        'slug': encodeDES('{}/{}'.format(campaign.pk, content.pk)),
        'faces_url': faces_url
    })
