from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.utils.sharingurls import build_urls
from core.utils.http import JsonHttpResponse
from targetshare.models import relational

from targetadmin import forms, utils


@utils.auth_client_required
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
        client_contents = client.clientcontent.all()
        if first_campaign:
            client_contents = client_contents.filter(campaignproperties__campaign=first_campaign)

        try:
            first_content = client_contents[0]
        except IndexError:
            first_content = None

    if first_campaign and first_content:
        context = {
            'snippet_form': forms.SnippetForm(client=client, initial={
                'campaign': first_campaign,
                'content': first_content,
            }),
        }
        context.update(build_urls(request.get_host(), first_campaign, first_content))
    else:
        context = {'snippet_form': forms.SnippetForm(client=client)}

    context.update(
        client=client,
        campaign=first_campaign,
        content=first_content,
    )
    return render(request, 'targetadmin/snippets.html', context)


@utils.auth_client_required
@require_GET
def snippet_update(request, client_pk):
    client = get_object_or_404(relational.Client, pk=client_pk)
    snippet_form = forms.SnippetForm(client=client, data=request.GET)

    if snippet_form.is_valid():
        campaign = snippet_form.cleaned_data['campaign']
        if request.GET.get('changed') == 'campaign':
            content = client.clientcontent.get(campaignproperties__campaign=campaign)
        else:
            content = snippet_form.cleaned_data['content']
        data = build_urls(request.get_host(), campaign, content)
        data.update(
            campaign=campaign.campaign_id,
            content=content.content_id,
        )
        return JsonHttpResponse(data)

    return JsonHttpResponse(snippet_form.errors, status=400)
