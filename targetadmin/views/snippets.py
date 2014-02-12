from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse

from targetadmin.utils import auth_client_required
from targetshare.models import relational
from targetshare.utils import encodeDES


@auth_client_required
def snippets(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    first_campaign = first_content = None
    if 'campaign_pk' in request.GET:
        first_campaign = get_object_or_404(
            relational.Campaign, pk=request.GET['campaign_pk'])

    if 'content_pk' in request.GET:
        first_content = get_object_or_404(
            relational.ClientContent, pk=request.GET['content_pk'])
    return render(request, 'targetadmin/snippets.html', {
        'client': client,
        'first_campaign': first_campaign or client.campaigns.all()[0],
        'first_content': first_content or client.clientcontent.all()[0]
    })


@auth_client_required
def encode_campaign(request, client_pk, campaign_pk, content_pk):
    get_object_or_404(relational.Client, pk=client_pk)
    get_object_or_404(relational.Campaign, pk=campaign_pk)
    get_object_or_404(relational.ClientContent, pk=content_pk)
    return HttpResponse(encodeDES('%s/%s' % (campaign_pk, content_pk)))
