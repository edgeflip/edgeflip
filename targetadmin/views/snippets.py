import urllib

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse

from targetadmin.utils import auth_client_required
from targetshare.models import relational
from targetshare.utils import encodeDES
from targetshare.views import utils


@auth_client_required
def snippets(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    first_campaign = first_content = None
    if 'campaign_pk' in request.GET:
        first_campaign = get_object_or_404(
            relational.Campaign, pk=request.GET['campaign_pk'])
    else:
        if client.campaigns.exists():
            first_campaign = client.campaigns.all()[0]

    if 'content_pk' in request.GET:
        first_content = get_object_or_404(
            relational.ClientContent, pk=request.GET['content_pk'])
    else:
        if client.clientcontent.exists():
            first_content = client.clientcontent.all()[0]

    first_faces_url = urllib.quote_plus('{}{}{}'.format(
        'https://' if request.is_secure() else 'http://',
        request.get_host(),
        reverse('incoming-encoded', args=[encodeDES('%s/%s' % (
            first_campaign.pk, first_content.pk))])
    ))
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
    faces_url = urllib.quote_plus('{}{}{}'.format(
        'https://' if request.is_secure() else 'http://',
        request.get_host(),
        reverse('incoming-encoded', args=[encodeDES('%s/%s' % (campaign.pk, content.pk))])
    ))
    return utils.JsonHttpResponse({
        'slug': encodeDES('{}/{}'.format(campaign.pk, content.pk)),
        'faces_url': faces_url
    })
