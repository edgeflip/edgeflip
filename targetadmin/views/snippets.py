from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse

from targetadmin.utils import internal
from targetshare.models import relational
from targetshare.utils import encodeDES


@internal
def snippets(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    return render(request, 'targetadmin/snippets.html', {
        'client': client,
        'first_campaign': client.campaigns.all()[0],
        'first_content': client.clientcontent.all()[0]
    })


@internal
def encode_campaign(request, client_pk, campaign_pk, content_pk):
    get_object_or_404(relational.Client, pk=client_pk)
    get_object_or_404(relational.Campaign, pk=campaign_pk)
    get_object_or_404(relational.ClientContent, pk=content_pk)
    return HttpResponse(encodeDES('%s/%s' % (campaign_pk, content_pk)))
